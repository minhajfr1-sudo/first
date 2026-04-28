# DRAPE — Virtual Try-On App

## Project Structure

```
vton-app/
├── src/
│   ├── App.jsx          ← entire frontend UI
│   ├── api.js           ← calls to Modal backend
│   ├── garments.js      ← your clothing library data
│   └── index.css        ← design tokens + resets
├── public/
│   └── garments/        ← PUT YOUR GARMENT IMAGES HERE
│       ├── california-tee.png
│       ├── denim-jacket.png
│       ├── navy-blazer.png
│       ├── grey-hoodie.png
│       ├── slim-jeans.png
│       ├── plaid-trousers.png
│       └── wide-leg-trousers.png
├── modal_app.py         ← Modal backend (deploy separately)
├── netlify.toml         ← Netlify build config
└── .env.example         ← copy to .env.local
```

---

## Step 1 — Add your garment images

Copy your 9 garment images into `public/garments/`.
Rename them to match the `image` field in `src/garments.js`.

---

## Step 2 — Deploy the Modal backend

```bash
pip install modal
modal setup          # authenticate
modal deploy modal_app.py
```

After deploy, Modal prints your endpoint URL:
```
https://YOUR-USERNAME--vton-demo-fastapi-app.modal.run
```

Copy it.

---

## Step 3 — Run frontend locally

```bash
cp .env.example .env.local
# Edit .env.local and paste your Modal URL

npm install
npm run dev
```

---

## Step 4 — Deploy to Netlify

1. Push this repo to GitHub
2. Go to netlify.com → New site from Git → pick your repo
3. Build command: `npm run build`
4. Publish directory: `dist`
5. Environment variables → add:
   ```
   VITE_MODAL_API_URL = https://YOUR-USERNAME--vton-demo-fastapi-app.modal.run
   ```
6. Deploy

---

## Adding More Garments

Edit `src/garments.js` — add an entry with:
- `id`: must match the garment filename in `/public/garments/` and in `/data/garments/` on Modal volume
- `type`: `"upper"` or `"lower"`
- `image`: path in `/public/garments/`

Then upload the garment PNG to your Modal volume:
```bash
modal volume put vton-data your-garment.png /garments/your-garment.png
```

---

## Notes on modal_app.py

The `modal_app.py` file contains stubs for the IDM-VTON and CatVTON pipelines.
The exact `pipe(...)` call parameters depend on the model version — refer to:
- IDM-VTON: https://huggingface.co/yisol/IDM-VTON
- CatVTON:  https://huggingface.co/zhengchong/CatVTON
