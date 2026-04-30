# (patched)
# Only showing modified parts for brevity

class VTONModel:

    @modal.enter()
    def load(self):
        import torch
        self.device   = "cuda"
        self.sessions: dict = {}
        self.base_images = {}  # NEW
        os.makedirs("/data/garments", exist_ok=True)
        self._load_seg_model()
        self._load_idm_vton()
        self._load_catvton()
        print("✅ All models ready")

    @modal.method()
    def generate_base_image(self, session_id: str):
        from PIL import Image
        import io

        if session_id not in self.sessions:
            raise ValueError("Session not found")

        img = Image.open(io.BytesIO(self.sessions[session_id])).convert("RGB")

        # TEMP base (replace with InstantID later)
        base_img = img.resize((768, 1024))

        self.base_images[session_id] = base_img
        return {"status": "base generated"}

    @modal.method()
    def tryon(self, session_id: str, garment_url: str, garment_type: str) -> str:
        import urllib.request
        from PIL import Image

        if session_id not in self.base_images:
            raise ValueError("Base image not generated")

        person_img = self.base_images[session_id]  # FIXED

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

# FastAPI add endpoint

@web_app.post("/generate-base-image")
def generate_base(req: dict):
    return model_instance.generate_base_image.remote(req["session_id"])
