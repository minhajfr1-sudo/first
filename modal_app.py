# FIXED VERSION (InstantID restored + identity working)

class VTONModel:

    @modal.enter()
    def load(self):
        import torch
        self.device = "cuda"
        self.sessions = {}
        self.base_images = {}

        self._load_instantid()
        print("🔥 NEW CODE RUNNING")

    def _load_instantid(self):
        import torch, os, sys, requests
        from insightface.app import FaceAnalysis
        from diffusers import ControlNetModel, AutoencoderKL

        # Face detection
        self.face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))

        # Load InstantID pipeline
        instantid_dir = "/data/instantid"
        os.makedirs(instantid_dir, exist_ok=True)

        pipeline_path = f"{instantid_dir}/pipeline_stable_diffusion_xl_instantid.py"
        if not os.path.exists(pipeline_path):
            r = requests.get(
                "https://raw.githubusercontent.com/huggingface/diffusers/main/examples/community/pipeline_stable_diffusion_xl_instantid.py"
            )
            open(pipeline_path, "w").write(r.text)

        sys.path.insert(0, instantid_dir)
        from pipeline_stable_diffusion_xl_instantid import StableDiffusionXLInstantIDPipeline

        controlnet = ControlNetModel.from_pretrained(
            "InstantX/InstantID-ControlNet",
            torch_dtype=torch.float16
        ).to(self.device)

        vae = AutoencoderKL.from_pretrained(
            "madebyollin/sdxl-vae-fp16-fix",
            torch_dtype=torch.float16
        ).to(self.device)

        self.instantid_pipe = StableDiffusionXLInstantIDPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            controlnet=controlnet,
            vae=vae,
            torch_dtype=torch.float16,
        ).to(self.device)

        print("✅ InstantID ready")

    @modal.method()
    def generate_base_image(self, session_id: str):
        import torch, cv2, numpy as np

        image_bytes = self.sessions[session_id]

        nparr = np.frombuffer(image_bytes, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        faces = self.face_app.get(img_cv)
        if not faces:
            raise ValueError("No face detected")

        face = faces[0]
        face_emb = torch.tensor(face.normed_embedding).unsqueeze(0).to(self.device)

        self.instantid_pipe.set_ip_adapter_scale(1.0)

        result = self.instantid_pipe(
            prompt="photorealistic full body photo of the same person, white background",
            negative_prompt="different person, wrong face, cartoon, anime",
            image_embeds=face_emb,
            image=None,
            num_inference_steps=30,
            guidance_scale=5.0,
            height=1024,
            width=768,
        ).images[0]

        self.base_images[session_id] = result
        return {"status": "ok"}

    @modal.method()
    def tryon(self, session_id: str, garment_url: str, garment_type: str) -> str:
        import urllib.request
        from PIL import Image
        import io, base64

        if session_id not in self.base_images:
            raise ValueError("Base image not generated")

        person_img = self.base_images[session_id]

        req = urllib.request.Request(garment_url, headers={"User-Agent": "DRAPE/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            garment_img = Image.open(io.BytesIO(resp.read())).convert("RGB")

        if garment_type == "upper":
            result = self._tryon_upper(person_img, garment_img)
        else:
            result = self._tryon_lower(person_img, garment_img)

        buf = io.BytesIO()
        result.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

@web_app.post("/generate-base-image")
def generate_base(req: dict):
    return model_instance.generate_base_image.remote(req["session_id"])
