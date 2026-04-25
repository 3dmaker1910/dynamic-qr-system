# Dynamic QR Code Manager 🔗

A lightweight FastAPI application for creating and managing **dynamic QR codes**.  
Each QR code points to a short URL (e.g. `https://yourapp.onrender.com/promo`) that redirects to a destination you can change at any time — without reprinting the QR.

---

## Features

- **Dynamic redirects** — update where a QR code points without regenerating the image.
- **Click tracking** — see how many times each QR code has been scanned.
- **QR image generation** — download PNG QR codes directly from the dashboard.
- **Admin dashboard** — clean Tailwind CSS UI to create, edit, list, and delete QR codes.
- **SQLite** — zero-config database, perfect for free-tier hosting.

---

## Quick Start (Local)

```bash
# 1. Clone the repo
git clone https://github.com/3dmaker1910/dynamic-qr-system.git
cd dynamic-qr-system

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
uvicorn main:app --reload

# 5. Open the dashboard
# http://localhost:8000/admin
```

---

## Deploy to Render (Free)

### Step 1 — Push to GitHub

```bash
cd dynamic-qr-system
git init
git add .
git commit -m "Initial commit - Dynamic QR system"
git branch -M main
git remote add origin https://github.com/3dmaker1910/dynamic-qr-system.git
git push -u origin main
```

### Step 2 — Create a Render Web Service

1. Go to [https://render.com](https://render.com) and sign in with GitHub.
2. Click **New → Web Service**.
3. Connect your `3dmaker1910/dynamic-qr-system` repo.
4. Configure:

   | Setting | Value |
   |---------|-------|
   | **Runtime** | Python |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
   | **Plan** | Free |

5. Click **Create Web Service**.

### Step 3 — Use it

- **Dashboard:** `https://your-app.onrender.com/admin`
- **Short URL example:** `https://your-app.onrender.com/promo`
- **API docs:** `https://your-app.onrender.com/docs`

> **Note:** On the free tier Render spins down after 15 min of inactivity.  
> The first request after sleep takes ~30 seconds. Upgrade to a paid plan to keep it always-on.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin` | Admin dashboard UI |
| `GET` | `/api/qr` | List all QR codes |
| `POST` | `/api/qr` | Create a QR code (`{slug, target_url}`) |
| `PUT` | `/api/qr/{slug}` | Update target URL (`{target_url}`) |
| `DELETE` | `/api/qr/{slug}` | Delete a QR code |
| `GET` | `/api/qr/{slug}/qrcode.png` | Download QR code PNG image |
| `GET` | `/{slug}` | Redirect to target URL (public) |
| `GET` | `/health` | Health check |

---

## Project Structure

```
dynamic-qr-system/
├── main.py              # FastAPI app with all endpoints
├── database.py          # SQLite database layer
├── templates/
│   └── index.html       # Admin dashboard (Tailwind CSS)
├── requirements.txt     # Python dependencies
├── Procfile             # Render start command
└── README.md            # This file
```

---

## License

MIT — do whatever you want with it.
