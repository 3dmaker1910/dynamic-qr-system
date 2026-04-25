import os
import pytest
from fastapi.testclient import TestClient

# Use a temp database for tests
os.environ["DATABASE_PATH"] = "test_qrcodes.db"

from main import app
from database import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    """Recreate the database for each test."""
    if os.path.exists("test_qrcodes.db"):
        os.remove("test_qrcodes.db")
    init_db()
    yield
    if os.path.exists("test_qrcodes.db"):
        os.remove("test_qrcodes.db")


# --- Health ---

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# --- Admin dashboard ---

def test_admin_page():
    r = client.get("/admin")
    assert r.status_code == 200
    assert "QR Code Manager" in r.text


# --- Create QR ---

def test_create_qr():
    r = client.post("/api/qr", json={"slug": "test1", "target_url": "https://example.com"})
    assert r.status_code == 201
    data = r.json()
    assert data["slug"] == "test1"
    assert data["target_url"] == "https://example.com"
    assert data["clicks" ] == 0
    assert "short_url" in data


def test_create_duplicate_slug():
    client.post("/api/qr", json={"slug": "dup", "target_url": "https://a.com"})
    r = client.post("/api/qr", json={"slug": "dup", "target_url": "https://b.com"})
    assert r.status_code == 409


def test_create_reserved_slug():
    r = client.post("/api/qr", json={"slug": "api", "target_url": "https://x.com"})
    assert r.status_code == 422


def test_create_invalid_url():
    r = client.post("/api/qr", json={"slug": "ok", "target_url": "not-a-url"})
    assert r.status_code == 422


def test_create_invalid_slug():
    r = client.post("/api/qr", json={"slug": "has spaces!", "target_url": "https://x.com"})
    assert r.status_code == 422


# --- List QRs ---

def test_list_empty():
    r = client.get("/api/qr")
    assert r.status_code == 200
    assert r.json()["qr_codes"] == []


def test_list_after_create():
    client.post("/api/qr", json={"slug": "a", "target_url": "https://a.com"})
    client.post("/api/qr", json={"slug": "b", "target_url": "https://b.com"})
    r = client.get("/api/qr")
    assert len(r.json()["qr_codes"]) == 2


# --- Update QR ---

def test_update_qr():
    client.post("/api/qr", json={"slug": "upd", "target_url": "https://old.com"})
    r = client.put("/api/qr/upd", json={"target_url": "https://new.com"})
    assert r.status_code == 200
    assert r.json()["target_url"] == "https://new.com"


def test_update_nonexistent():
    r = client.put("/api/qr/nope", json={"target_url": "https://x.com"})
    assert r.status_code == 404


# --- Delete QR ---

def test_delete_qr():
    client.post("/api/qr", json={"slug": "del", "target_url": "https://del.com"})
    r = client.delete("/api/qr/del")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    r2 = client.get("/api/qr")
    assert len(r2.json()["qr_codes"]) == 0


def test_delete_nonexistent():
    r = client.delete("/api/qr/ghost")
    assert r.status_code == 404


# --- Redirect ---

def test_redirect():
    client.post("/api/qr", json={"slug": "go", "target_url": "https://example.com/dest"})
    r = client.get("/go", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "https://example.com/dest"


def test_redirect_increments_clicks():
    client.post("/api/qr", json={"slug": "clk", "target_url": "https://example.com"})
    client.get("/clk", follow_redirects=False)
    client.get("/clk", follow_redirects=False)
    r = client.get("/api/qr")
    qr = [q for q in r.json()["qr_codes"] if q["slug" ] == "clk"][0]
    assert qr["clicks"] == 2


def test_redirect_not_found():
    r = client.get("/nonexistent", follow_redirects=False)
    assert r.status_code == 404


# --- QR Code image ---

def test_qr_image():
    client.post("/api/qr", json={"slug": "img", "target_url": "https://example.com"})
    r = client.get("/api/qr/img/qrcode.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert len(r.content) > 100


def test_qr_image_not_found():
    r = client.get("/api/qr/nope/qrcode.png")
    assert r.status_code == 404
