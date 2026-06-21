# Deploy EventOps for a public demo URL

Two options: **Streamlit Community Cloud** (recommended for hackathon submission) or **ngrok** (instant temporary URL).

---

## Option A — Streamlit Community Cloud (recommended)

### 1. Initialize git in the project folder only

```powershell
cd "c:\Users\verma\Downloads\Flipkart Gridlock Prototype"
git init
git add .
git commit -m "EventOps Theme 2 prototype for Gridlock hackathon"
```

Ensure `.env` is **not** committed (already in `.gitignore`).

### 2. Push to GitHub

Create a new repo on GitHub, then:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/eventops-gridlock.git
git branch -M main
git push -u origin main
```

### 3. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. **New app** → connect GitHub repo
3. **Main file:** `app.py`
4. **Secrets** (Settings → Secrets):

```toml
MAPMYINDIA_API_KEY = "0ae5e508b5e5980945bcea8f3c43ba56"
MAPPLS_CLIENT_ID = "your_client_id"
MAPPLS_CLIENT_SECRET = "your_client_secret"
```

5. Deploy — first load runs `bootstrap.py` (~1–2 min to train models)

Your public URL will look like:  
`https://YOUR-APP-NAME.streamlit.app`

Paste that URL into your hackathon submission and `SUBMISSION.md`.

---

## Option B — ngrok (instant, temporary)

While Streamlit is running locally:

```powershell
# Terminal 1
python -m streamlit run app.py

# Terminal 2
ngrok http 8501
```

Copy the `https://….ngrok-free.app` URL into your submission.

> ngrok free URLs expire when you close the tunnel — use Streamlit Cloud for judges who review later.

---

## Map note for deployed app

Mappls maps may appear blank inside Streamlit iframe on some browsers. In the sidebar, click **Open Mappls map in new tab** — the full-screen map works reliably.

---

## Included artifacts for cloud boot

These ship with the repo so deploy works without manual training:

- `data/prepared_events.parquet`
- `data/models/*.json`, `data/models/*.parquet`
- Raw CSV for retrain

Models (`.joblib`) are gitignored — `bootstrap.py` retrains them on first cloud boot.
