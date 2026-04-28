"""
DRAPE — Modal Backend (Complete & Correct)
==========================================
Deploy:  modal deploy modal_app.py
Your URL will look like:
  https://YOUR-USERNAME--vton-demo-fastapi-app.modal.run

Set that as VITE_MODAL_API_URL in Netlify env vars.

Architecture:
  - IDM-VTON  → upper body (SDXL-based, best garment fidelity)
  - CatVTON   → lower body (SD1.5-based, handles pants/skirts)
  - SegFormer  → mask generation for lower body (no detectron2 needed)
  - ONNX humanparsing + OpenPose from IDM-VTON repo (baked into image)
"""

import io
import os
import sys
import uuid
import base64
import numpy as np
import modal
from pathlib import Path

# ── App + Volume ─────────────────────────────────────────────────────────────
app    = modal.App("vton-demo")
volume = modal.Volume.from_name("vton-data", create_if_missing=True)

# ── Image ─────────────────────────────────────────────────────────────────────
# Bakes in: repos, ONNX humanparsing models, OpenPose weights.
# Large HuggingFace model weights go in the Volume (downloaded at first run).

vton_image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install(
        "git", "wget",
        "libgl1-mesa-glx", "libglib2.0-0",
        "libsm6", "libxext6", "libxrender-dev",
        "ffmpeg", "libgomp1",
    )
    .pip_install(
        "torch==2.1.2",
        "torchvision==0.16.2",
        index_url="https://download.pytorch.org/whl/cu118",
    )
    .pip_install(
        "diffusers==0.25.1",
        "transformers==4.37.2",
        "accelerate==0.26.1",
        "safetensors==0.4.2",
        "huggingface_hub==0.20.3",
        "controlnet-aux==0.0.7",
        "einops",
        "timm==0.9.12",
        "Pillow==10.2.0",
        "opencv-python-headless==4.9.0.80",
        "scikit-image==0.22.0",
        "scipy",
        "onnxruntime-gpu==1.17.0",
        "onnx",
        "fastapi==0.109.2",
        "uvicorn[standard]==0.27.0",
        "python-multipart==0.0.9",
        "omegaconf",
        "tqdm",
    )
    .run_commands(
        # Clone IDM-VTON (provides TryonPipeline + humanparsing + OpenPose)
        "git clone https://github.com/yisol/IDM-VTON /IDM-VTON",

        # Clone CatVTON (provides CatVTONPipeline for lower body)
        "git clone https://github.com/Zheng-Chong/CatVTON /CatVTON",

        # Create checkpoint dirs
        "mkdir -p /IDM-VTON/ckpt/humanparsing",
        "mkdir -p /IDM-VTON/ckpt/openpose/ckpts",

        # Human parsing ONNX models (baked into image, ~30 MB each)
        "wget -q -O /IDM-VTON/ckpt/humanparsing/parsing_atr.onnx "
        "https://huggingface.co/spaces/yisol/IDM-VTON/resolve/main/ckpt/humanparsing/parsing_atr.onnx",

        "wget -q -O /IDM-VTON/ckpt/humanparsing/parsing_lip.onnx "
        "https://huggingface.co/spaces/yisol/IDM-VTON/resolve/main/ckpt/humanparsing/parsing_lip.onnx",

        # OpenPose body pose model (baked into image, ~200 MB)
        "wget -q -O /IDM-VTON/ckpt/openpose/ckpts/body_pose_model.pth "
        "https://huggingface.co/spaces/yisol/IDM-VTON/resolve/main/ckpt/openpose/ckpts/body_pose_model.pth",
    )
    .env({
        "PYTHONPATH": "/IDM-VTON:/CatVTON",
    })
)


# ── Shared mask helper (used for lower body via SegFormer) ───────────────────

def get_segformer_mask(seg_processor, seg_model, person_img, labels, device):
    """
    Run SegFormer clothing segmentation and return binary PIL mask.
    labels: list of class indices to include in mask.
    Returns PIL 'L' image (255 = replace, 0 = keep).
    """
    import torch
    import torch.nn.functional as F
    from PIL import Image

    inputs = seg_processor(images=person_img, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = seg_model(**inputs)

    logits = F.interpolate(
        outputs.logits,
        size=(person_img.height, person_img.width),
        mode="bilinear",
        align_corners=False,
    )
    seg = logits.argmax(dim=1).squeeze().cpu().numpy().astype(np.uint8)
    mask = np.isin(seg, labels).astype(np.uint8) * 255
    return Image.fromarray(mask, mode="L")


# ── Modal model class ─────────────────────────────────────────────────────────

@app.cls(
    gpu="A10G",
    image=vton_image,
    container_idle_timeout=300,
    volumes={"/data": volume},
    timeout=300,
)
class VTONModel:

    @modal.enter()
    def load(self):
        import torch
        self.device   = "cuda"
        self.sessions: dict = {}
        os.makedirs("/data/garments", exist_ok=True)
        self._load_seg_model()
        self._load_idm_vton()
        self._load_catvton()
        print("✅ All models ready")

    # ── SegFormer (shared mask generator) ────────────────────────────────────

    def _load_seg_model(self):
        from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
        print("Loading SegFormer…")
        self.seg_processor = SegformerImageProcessor.from_pretrained(
            "mattmdjaga/segformer_b2_clothes"
        )
        self.seg_model = SegformerForSemanticSegmentation.from_pretrained(
            "mattmdjaga/segformer_b2_clothes",
        ).to(self.device).eval()
        print("✅ SegFormer ready")

    # ── IDM-VTON (upper body) ─────────────────────────────────────────────────

    def _load_idm_vton(self):
        import torch
        from huggingface_hub import snapshot_download
        from src.tryon_pipeline import StableDiffusionXLInpaintPipeline as TryonPipeline
        from src.unet_hacked_garmnet import UNet2DConditionModel as UNet2DConditionModel_ref
        from src.unet_hacked_tryon import UNet2DConditionModel
        from transformers import (
            CLIPImageProcessor, CLIPVisionModelWithProjection,
            CLIPTextModel, CLIPTextModelWithProjection, AutoTokenizer,
        )
        from diffusers import DDPMScheduler, AutoencoderKL

        model_dir = "/data/models/idm-vton"
        if not Path(model_dir).exists():
            print("Downloading IDM-VTON weights (~5 GB, first run only)…")
            snapshot_download("yisol/IDM-VTON", local_dir=model_dir)

        print("Loading IDM-VTON pipeline…")

        unet = UNet2DConditionModel.from_pretrained(
            model_dir, subfolder="unet", torch_dtype=torch.float16
        ).to(self.device)
        unet.requires_grad_(False)

        unet_encoder = UNet2DConditionModel_ref.from_pretrained(
            model_dir, subfolder="unet_encoder", torch_dtype=torch.float16
        ).to(self.device)
        unet_encoder.requires_grad_(False)

        image_encoder = CLIPVisionModelWithProjection.from_pretrained(
            model_dir, subfolder="image_encoder", torch_dtype=torch.float16
        ).to(self.device)
        image_encoder.requires_grad_(False)

        vae = AutoencoderKL.from_pretrained(
            model_dir, subfolder="vae", torch_dtype=torch.float16
        ).to(self.device)

        text_encoder_one = CLIPTextModel.from_pretrained(
            model_dir, subfolder="text_encoder", torch_dtype=torch.float16
        ).to(self.device)

        text_encoder_two = CLIPTextModelWithProjection.from_pretrained(
            model_dir, subfolder="text_encoder_2", torch_dtype=torch.float16
        ).to(self.device)

        tokenizer_one = AutoTokenizer.from_pretrained(
            model_dir, subfolder="tokenizer", use_fast=False
        )
        tokenizer_two = AutoTokenizer.from_pretrained(
            model_dir, subfolder="tokenizer_2", use_fast=False
        )

        self.idm_pipe = TryonPipeline.from_pretrained(
            model_dir,
            unet=unet,
            vae=vae,
            feature_extractor=CLIPImageProcessor(),
            text_encoder=text_encoder_one,
            text_encoder_2=text_encoder_two,
            tokenizer=tokenizer_one,
            tokenizer_2=tokenizer_two,
            scheduler=DDPMScheduler.from_pretrained(model_dir, subfolder="scheduler"),
            image_encoder=image_encoder,
            torch_dtype=torch.float16,
            add_watermarker=False,
        ).to(self.device)

        # unet_encoder extracts garment features; attached separately
        self.idm_pipe.unet_encoder = unet_encoder

        # IDM-VTON's ONNX humanparsing (checkpoint baked into image)
        from preprocess.humanparsing.run_parsing import Parsing
        self.parsing = Parsing(0)

        # IDM-VTON's OpenPose wrapper (checkpoint baked into image)
        from preprocess.openpose.run_openpose import OpenPose
        self.openpose = OpenPose(0)

        print("✅ IDM-VTON ready")

    # ── CatVTON (lower body) ──────────────────────────────────────────────────

    def _load_catvton(self):
        import torch
        from model.pipeline import CatVTONPipeline

        model_dir = "/data/models/catvton"
        if not Path(model_dir).exists():
            from huggingface_hub import snapshot_download
            print("Downloading CatVTON weights (~1.5 GB, first run only)…")
            snapshot_download("zhengchong/CatVTON", local_dir=model_dir)

        print("Loading CatVTON pipeline…")
        self.catvton_pipe = CatVTONPipeline(
            attn_ckpt_version="mix",
            attn_ckpt=model_dir,
            base_ckpt="booksforcharlie/stable-diffusion-inpainting",
            weight_dtype=torch.float16,
            device=self.device,
            skip_safety_check=True,
        )
        print("✅ CatVTON ready")

    # ── Mask + pose generation ────────────────────────────────────────────────

    def _get_upper_mask_and_pose(self, person_img):
        """
        IDM-VTON's own ONNX humanparsing + OpenPose.
        Returns (mask: PIL 'L', pose_img: PIL RGB) both at 768×1024.
        """
        from utils_mask import get_mask_location   # in /IDM-VTON

        small = person_img.resize((384, 512))
        keypoints   = self.openpose(small)
        model_parse, _ = self.parsing(small)

        mask, _ = get_mask_location("hd", "upper_body", model_parse, keypoints)
        mask = mask.resize((768, 1024))

        # Rendered pose image is returned as keypoints["pose_image"] by OpenPose
        pose_img = keypoints["pose_image"].resize((768, 1024))

        return mask, pose_img

    def _get_lower_mask(self, person_img):
        """SegFormer-based lower-body mask. No detectron2 needed."""
        # 5=skirt, 6=pants, 12=left-leg, 13=right-leg
        return get_segformer_mask(
            self.seg_processor, self.seg_model,
            person_img, [5, 6, 12, 13], self.device
        )

    # ── Try-on methods ────────────────────────────────────────────────────────

    def _tryon_upper(self, person_img, garment_img):
        import torch
        import torchvision.transforms as T

        W, H = 768, 1024
        person_img  = person_img.resize((W, H))
        garment_img = garment_img.resize((W, H))

        mask, pose_img = self._get_upper_mask_and_pose(person_img)

        norm = T.Compose([T.ToTensor(), T.Normalize([0.5], [0.5])])
        garm_tensor = norm(garment_img).unsqueeze(0).to(self.device, torch.float16)
        pose_tensor = norm(pose_img).unsqueeze(0).to(self.device, torch.float16)

        prompt          = "a photo of a model wearing a garment"
        negative_prompt = "monochrome, lowres, bad anatomy, worst quality, low quality"

        with torch.no_grad():
            with torch.cuda.amp.autocast():
                (
                    prompt_embeds,
                    negative_prompt_embeds,
                    pooled_prompt_embeds,
                    negative_pooled_prompt_embeds,
                ) = self.idm_pipe.encode_prompt(
                    prompt,
                    num_images_per_prompt=1,
                    do_classifier_free_guidance=True,
                    negative_prompt=negative_prompt,
                )

                prompt_embeds_c, _, _, _ = self.idm_pipe.encode_prompt(
                    "a photo of a garment",
                    num_images_per_prompt=1,
                    do_classifier_free_guidance=False,
                    negative_prompt=negative_prompt,
                )

                result = self.idm_pipe(
                    prompt_embeds=prompt_embeds.to(self.device, torch.float16),
                    negative_prompt_embeds=negative_prompt_embeds.to(self.device, torch.float16),
                    pooled_prompt_embeds=pooled_prompt_embeds.to(self.device, torch.float16),
                    negative_pooled_prompt_embeds=negative_pooled_prompt_embeds.to(self.device, torch.float16),
                    num_inference_steps=30,
                    generator=torch.Generator(self.device).manual_seed(42),
                    strength=1.0,
                    pose_img=pose_tensor,
                    text_embeds_cloth=prompt_embeds_c.to(self.device, torch.float16),
                    cloth=garm_tensor,
                    mask_image=mask,
                    image=person_img,
                    height=H,
                    width=W,
                    ip_adapter_image=garment_img,
                    guidance_scale=2.0,
                )[0]    # list of PIL images

        return result

    def _tryon_lower(self, person_img, garment_img):
        import torch
        from utils import resize_and_crop, resize_and_padding   # in /CatVTON

        W, H = 768, 1024
        person_img  = resize_and_padding(person_img, (W, H))
        garment_img = resize_and_crop(garment_img,  (W, H))

        mask = self._get_lower_mask(person_img)

        result = self.catvton_pipe(
            image=person_img,
            condition_image=garment_img,
            mask=mask,
            num_inference_steps=50,
            guidance_scale=2.5,
            generator=torch.Generator("cuda").manual_seed(42),
        )[0]

        return result

    # ── Public Modal methods ───────────────────────────────────────────────────

    @modal.method()
    def process_photo(self, image_bytes: bytes) -> dict:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = image_bytes
        return {"session_id": session_id}

    @modal.method()
    def tryon(self, session_id: str, garment_url: str, garment_type: str) -> str:
        """
        Returns base64-encoded PNG of the try-on result.
        garment_url: public Netlify URL e.g.
                     https://your-app.netlify.app/garments/denim-jacket.png
        """
        import urllib.request
        from PIL import Image

        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")

        person_img = Image.open(io.BytesIO(self.sessions[session_id])).convert("RGB")

        # Fetch garment image directly from Netlify — no manual upload step
        try:
            req = urllib.request.Request(garment_url, headers={"User-Agent": "DRAPE/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                garment_img = Image.open(io.BytesIO(resp.read())).convert("RGB")
        except Exception as e:
            raise ValueError(f"Could not fetch garment from {garment_url}: {e}")

        if garment_type == "upper":
            result = self._tryon_upper(person_img, garment_img)
        elif garment_type == "lower":
            result = self._tryon_lower(person_img, garment_img)
        else:
            raise ValueError(f"garment_type must be 'upper' or 'lower'")

        buf = io.BytesIO()
        result.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()


# ── FastAPI ───────────────────────────────────────────────────────────────────
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

web_app = FastAPI(title="DRAPE API")
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # lock to your Netlify URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

model_instance = VTONModel()


@web_app.get("/ping")
def ping():
    """Warm-up call — frontend fires this on photo upload."""
    return {"status": "warm"}


@web_app.post("/process-photo")
async def process_photo(person_image: UploadFile = File(...)):
    image_bytes = await person_image.read()
    try:
        return model_instance.process_photo.remote(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TryOnRequest(BaseModel):
    session_id: str
    garment_url: str      # full public URL to garment PNG on Netlify
    garment_type: str     # "upper" | "lower"


@web_app.post("/tryon")
def tryon(req: TryOnRequest):
    try:
        b64 = model_instance.tryon.remote(req.session_id, req.garment_url, req.garment_type)
        return {"result_image": b64}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.function(image=vton_image)
@modal.asgi_app()
def fastapi_app():
    return web_app
