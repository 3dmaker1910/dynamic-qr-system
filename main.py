import io
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator
import qrcode

from database import init_db, create_qr, update_qr, get_qr, list_qrs, increment_clicks, delete_qr

SLUG_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
RESERVED_SLUGS = {"api", "admin", "static", "health", "favicon.ico"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Dynamic QR Code Manager", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


# --- Pydantic models ---

class QRCreate(BaseModel):
    slug: str
    target_url: str

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip()
        if v.lower() in RESERVED_SLUGS:
            raise ValueError(f"'{v}' is a reserved slug")
        if not SLUG_RE.match(v):
            raise ValueError("Slug must be 1-64 chars: letters, digits, hyphens, underscores")
        return v

    @field_validator("target_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class QRUpdate(BaseModel):
    target_url: str

    @field_validator("target_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


# --- Admin dashboard ---

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return templates.TemplateResponse(request, "index.html")


# --- API endpoints ---

@app.get("/api/qr")
def api_list_qrs(request: Request):
    qrs = list_qrs()
    base = str(request.base_url).rstrip("/")
    for q in qrs:
        q["short_url"] = f"{base}/{q['slug']}"
    return {"qr_codes": qrs}


@app.post("/api/qr", status_code=201)
def api_create_qr(payload: QRCreate, request: Request):
    existing = get_qr(payload.slug)
    if existing:
        raise HTTPException(status_code=409, detail="Slug already exists")
    row = create_qr(payload.slug, payload.target_url)
    base = str(request.base_url).rstrip("/")
    row["short_url"] = f"{base}/{row['slug']}"
    return row


@app.put("/api/qr/{slug}")
def api_update_qr(slug: str, payload: QRUpdate):
    row = update_qr(slug, payload.target_url)
    if row is None:
        raise HTTPException(status_code=404, detail="Slug not found")
    return row


@app.delete("/api/qr/{slug}")
def api_delete_qr(slug: str):
    if not delete_qr(slug):
        raise HTTPException(status_code=404, detail="Slug not found")
    return {"ok": True}


@app.get("/api/qr/{slug}/qrcode.png")
def api_qr_image(slug: str, request: Request):
    row = get_qr(slug)
    if row is None:
        raise HTTPException(status_code=404, detail="Slug not found")
    base = str(request.base_url).rstrip("/")
    short_url = f"{base}/{slug}"
    img = qrcode.make(short_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


# --- Health check ---

@app.get("/health")
def health():
    return {"status": "ok"}


# --- Redirect endpoint (must be last) ---

@app.get("/{slug}")
def redirect_slug(slug: str):
    if slug in RESERVED_SLUGS or slug == "admin":
        raise HTTPException(status_code=404, detail="Not found")
    row = get_qr(slug)
    if row is None:
        raise HTTPException(status_code=404, detail="QR code not found")
    increment_clicks(slug)
    return RedirectResponse(url=row["target_url"], status_code=307)
