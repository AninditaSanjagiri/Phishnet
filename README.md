# PhishNet 🛡️
### Multimodal Phishing Detection — URL + Text + Visual AI

A college-level project demonstrating **late-fusion multimodal phishing detection** using three lightweight, free models running in parallel. Directly addresses two key research gaps identified in recent literature: adversarial evasion of single-modality detectors, and deployment viability on constrained infrastructure.

---

## Architecture at a Glance

```
User submits URL
       │
       ▼
  FastAPI Backend
       │
  asyncio.gather()  ─────────────────────────────────┐
       │                                              │
       ▼                                              ▼
  URL Agent                Text Agent           Image Agent
  RandomForest             DistilBERT           MobileNetV3
  ~2ms                     ~80ms                ~120ms (+ screenshot)
       │                       │                     │
       └──────────── FusionAgent ──────────────────────┘
                    Weighted Late Fusion
                           │
                     Final Verdict
              (phishing / suspicious / safe)
                    + Explanation
```

---

## Tech Stack (100% Free)

| Layer | Tool |
|---|---|
| Frontend | React 18 + Vite + custom CSS |
| Backend | Python 3.11 + FastAPI + asyncio |
| URL model | Scikit-learn RandomForest |
| Text model | `ealvaradob/bert-finetuned-phishing` (HuggingFace) |
| Image model | MobileNetV3-Small (PyTorch + torchvision) |
| Screenshots | Playwright headless Chromium |
| Database | SQLite via SQLAlchemy async |
| Frontend deploy | Vercel (free hobby) |
| Backend deploy | Render (free web service) |

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. Clone and set up backend

```bash
git clone https://github.com/yourname/phishnet
cd phishnet/backend

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Install headless Chromium for screenshots
playwright install chromium
playwright install-deps chromium   # Linux only

cp .env.example .env
```

### 2. Set up frontend

```bash
cd ../frontend
npm install
cp .env.example .env.local
```

### 3. Start both servers

**Terminal 1 — Backend:**
```bash
cd backend
source .venv/bin/activate
python main.py
# → Running on http://localhost:8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
# → Running on http://localhost:5173
```

Open **http://localhost:5173** and paste any URL to analyze.

---

## Training the Models

### Phase 1: URL Model (Random Forest)

The system ships with a synthetic baseline model that auto-generates on first run. To train on real data:

**Download datasets:**
- PhishTank: https://phishtank.org/developer_info.php → `verified_online.csv`
- Tranco top-1M: https://tranco-list.eu → `top-1m.csv`

```bash
cd backend
python train_url_model.py \
  --phishtank data/verified_online.csv \
  --legit     data/top-1m.csv \
  --output    models/url_rf_model.joblib
```

Expected accuracy: **~94–97%** on balanced test set.

---

### Phase 2: Screenshot Dataset

Build the image dataset using Playwright batch capture:

```bash
# Get phishing URLs from PhishTank (export as text, one URL per line)
python capture_screenshots.py \
  --urls  data/phish_urls.txt \
  --output data/screenshots/phishing \
  --limit 2000 \
  --concurrency 5

# Get legit URLs from Tranco top-1k
python capture_screenshots.py \
  --urls  data/legit_urls.txt \
  --output data/screenshots/legitimate \
  --limit 2000
```

Your dataset structure should look like:
```
data/screenshots/
  phishing/     ← ~2000 PNG screenshots of phishing pages
  legitimate/   ← ~2000 PNG screenshots of legit pages
```

---

### Phase 3: Image Model (MobileNetV3)

```bash
python train_image_model.py \
  --data   data/screenshots \
  --epochs 10 \
  --output models/image_mobilenet.pth
```

Expected accuracy after 10 epochs: **~88–93%** depending on dataset quality.
Training time: ~25 min on CPU, ~4 min on GPU.

---

### Phase 4: Fusion Model (Logistic Regression)

After training URL and image models, generate predictions on a held-out validation set and train the fusion layer:

```bash
# Collect val set predictions from all three agents and save to CSV
python generate_fusion_dataset.py \
  --urls data/val_urls.txt \
  --output data/fusion_train.csv

# Train the logistic regression fusion layer
python train_fusion_model.py \
  --data   data/fusion_train.csv \
  --output models/fusion_lr.joblib
```

See `train_fusion_model.py` for the full script (simple 3-feature logistic regression).

---

## Datasets

| Dataset | Use | Link |
|---|---|---|
| PhishTank | URL + image (phishing) | phishtank.org |
| Tranco Top-1M | URL + image (legit) | tranco-list.eu |
| UCI Phishing Websites | URL features | archive.ics.uci.edu/dataset/327 |
| CLAIR Nazario Dataset | Email text phishing | GitHub: CLAIR-phishing |
| SpamAssassin | Email text legit | spamassassin.apache.org |

---

## API Reference

### `POST /analyze`

```json
// Request
{ "url": "https://example.com" }

// Response
{
  "url": "https://example.com",
  "verdict": "safe",               // "phishing" | "suspicious" | "safe"
  "phishing_probability": 12.4,   // 0–100
  "processing_time_ms": 1243.5,
  "url_agent": {
    "score": 0.08,
    "confidence": 0.94,
    "explanation": "URL structure looks normal.",
    "features": { ... }
  },
  "text_agent": { ... },
  "image_agent": { ... },
  "fusion_weights": {
    "url": 0.35, "text": 0.40, "image": 0.25,
    "method": "static_weighted_average"
  },
  "screenshot_base64": "...",
  "gradcam_base64": "..."
}
```

### `GET /history?limit=20`
Returns the last N analysis logs from the database.

### `GET /health`
Returns `{"status": "ok"}` — used by Render health checks.

---

## Deployment

### Frontend → Vercel

```bash
cd frontend
npm run build   # verify build passes locally first

# Install Vercel CLI (free)
npm install -g vercel
vercel login
vercel --prod

# Set environment variable in Vercel dashboard:
# VITE_API_BASE = https://your-render-app.onrender.com
```

### Backend → Render

1. Push to GitHub
2. Go to https://render.com → New Web Service
3. Connect your GitHub repo
4. Settings:
   - **Root directory:** `backend`
   - **Build command:** `pip install -r requirements.txt && playwright install chromium && playwright install-deps chromium`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
5. Add environment variables matching `.env.example`
6. Deploy

> ⚠️ Render free tier sleeps after 15 min of inactivity. First request after sleep takes ~30s. Acceptable for demo/college use.

### Alternative: HuggingFace Spaces (Gradio)

For a simpler demo without separate frontend/backend, deploy as a Gradio app on HuggingFace Spaces (free, GPU available):

```bash
cd backend
# Add gradio_app.py (see docs/gradio_app.py)
# Push to a new HuggingFace Space
```

---

## Project Structure

```
phishnet/
├── backend/
│   ├── main.py                   # FastAPI app + routes
│   ├── database.py               # SQLite async ORM
│   ├── requirements.txt
│   ├── .env.example
│   ├── agents/
│   │   ├── orchestrator.py       # asyncio.gather() coordinator
│   │   ├── url_agent.py          # RF classifier + 16 URL features
│   │   ├── text_agent.py         # DistilBERT + HTML parsing
│   │   ├── image_agent.py        # MobileNetV3 + GradCAM
│   │   └── fusion_agent.py       # Weighted late fusion
│   ├── models/                   # Saved .joblib and .pth files (gitignored)
│   ├── data/                     # Datasets and screenshots (gitignored)
│   ├── train_url_model.py
│   ├── train_image_model.py
│   └── capture_screenshots.py
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx / App.css
│       ├── index.css
│       ├── components/
│       │   ├── Header.jsx/css
│       │   ├── AnalyzerView.jsx/css
│       │   ├── URLInput.jsx/css
│       │   ├── VerdictBanner.jsx/css
│       │   ├── AgentCard.jsx/css
│       │   ├── FusionPanel.jsx/css
│       │   ├── ScreenshotPanel.jsx/css
│       │   ├── LoadingState.jsx/css
│       │   └── HistoryView.jsx/css
│       └── utils/
│           └── api.js
│
├── render.yaml
├── vercel.json
├── .gitignore
└── README.md
```

---

## Research Gaps Addressed

This project directly targets two gaps from the survey literature:

**Gap 1 — Adversarial evasion of single-modality detectors**
Attackers embed text in images, or visually clone legitimate sites to defeat text-only or vision-only scanners. PhishNet runs all three modalities independently and fuses them — a high image score can flag pages that have clean HTML.

**Gap 2 — Deployment viability**
Heavy LLM-based systems introduce 5–15s delays (cited in survey). PhishNet's entire stack — RF (2ms) + DistilBERT (80ms) + MobileNetV3 (120ms) running in parallel — completes in under 200ms on CPU, excluding screenshot capture which runs concurrently.

---

## Explainability (XAI)

Each agent contributes a plain-English explanation:
- **URL agent:** Top 3 triggered features (e.g. "domain mimics known brand; high URL entropy")
- **Text agent:** Form metadata signals + DistilBERT classification
- **Image agent:** GradCAM heatmap overlay showing which regions triggered the visual classifier

This directly addresses the survey's "black-box" criticism.

---

## Limitations and Future Work

- The image model requires a real screenshot dataset for production accuracy (synthetic baseline is weak)
- Multilingual pages default to keyword heuristics only
- QR code / SMS phishing not yet supported
- Fusion weights are static unless a fusion LR model is trained on real data
- Render free tier cold-start latency (~30s) is not suitable for real-time SOC integration

---

## Credits

- [PhishTank](https://phishtank.org) — phishing URL feed
- [ealvaradob/bert-finetuned-phishing](https://huggingface.co/ealvaradob/bert-finetuned-phishing) — DistilBERT checkpoint
- [Playwright](https://playwright.dev/python/) — headless browser screenshots
- Research gaps sourced from: *"Enhanced phishing detection using multimodal data"* (ScienceDirect 2025) and related survey literature

---

*Built as a college-level demonstration of multimodal AI systems. Not intended for production security use without additional hardening.*
