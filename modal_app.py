# PATCHED VERSION (identity fix + GPU fix)

class VTONModel:

    @modal.enter()
    def load(self):
        import torch
        self.device   = "cuda"
        self.sessions: dict = {}
        self.base_images = {}
        os.makedirs("/data/garments", exist_ok=True)
        self._load_seg_model()
        self._load_idm_vton()
        self._load_catvton()
        self._load_instantid()
        print("✅ All models ready")

    def _load_instantid(self):
        from insightface.app import FaceAnalysis

        # 🔥 GPU FIX
        self.face_app = FaceAnalysis(
            name="buffalo_l",
            providers=["CUDAExecutionProvider"],
        )
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))

    @modal.method()
    def generate_base_image(self, session_id: str):
        from PIL import Image
        import io, torch, cv2, numpy as np

        if session_id not in self.sessions:
            raise ValueError("Session not found")

        image_bytes = self.sessions[session_id]

        nparr = np.frombuffer(image_bytes, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        faces = self.face_app.get(img_cv)
        if not faces:
            raise ValueError("No face detected")

        face = faces[0]

        # 🔥 FIXED EMBEDDING
        face_emb = torch.tensor(face.normed_embedding).unsqueeze(0).to(self.device)

        prompt = (
            "realistic full body photo of the SAME person, standing straight, neutral pose, plain white background, natural lighting"
        )

        negative_prompt = (
            "different person, wrong face, cartoon, anime, illustration, fake face, deformed, blurry"
        )

        self.instantid_pipe.set_ip_adapter_scale(1.0)

        with torch.no_grad():
            base_img = self.instantid_pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image_embeds=face_emb,
                image=None,  # 🔥 KEY FIX
                num_inference_steps=30,
                guidance_scale=4.5,
                height=1024,
                width=768,
            ).images[0]

        self.base_images[session_id] = base_img
        return {"status": "base generated"}

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
