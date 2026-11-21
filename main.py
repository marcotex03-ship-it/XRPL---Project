import os
import sys
import json
import hashlib
import random
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")

USERS_FILE = ROOT_DIR / "users.json"


def _load_users() -> dict:
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_users(users: dict):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        print(f"[WARN] Failed to write users to disk: {e}")


class AuthRequest(BaseModel):
    username: str
    password: str
    wallet_address: Optional[str] = None

from simulator.simulate_spotify import (
    ARTISTS_DB,
    simulate_user_streams,
    compute_top_listener_vector,
)

# Real XRPL Layer imports
from xrpl_layer.xrpl_service import (
    issue_card_for_fan,
    verify_card_validity,
    redeem_and_burn_card,
)
from xrpl_layer.pool_service import (
    generate_artist_pool,
    claim_card_from_pool,
    get_pool_status,
    _load_pool,
    _save_pool,
)

app = FastAPI(title="SuperFan - XRPL Hackathon")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory card cache per user session
USER_CARDS_DB: dict[str, list[dict]] = {}


class RedeemRequest(BaseModel):
    username: str
    artist_name: str
    perk_type: str  # "merch" or "ticketmaster"


class PoolGenerateRequest(BaseModel):
    artist_name: str
    count: int = 2  # default 2 for fast demo testing


# ==========================================================
# AUTH ENDPOINTS
# ==========================================================

@app.post("/api/auth/register")
def register_user(req: AuthRequest):
    username = req.username.strip()
    if not username or not req.password:
        raise HTTPException(status_code=400, detail="Username e password sono obbligatori.")

    users = _load_users()
    for u in users:
        if u.lower() == username.lower():
            raise HTTPException(status_code=400, detail="Questo username è già registrato. Accedi con le tue credenziali.")

    default_fan_wallet = os.getenv("FAN_ADDRESS", "rDrVhthSnhAv4YKUjskJ5v8KiQsQdeWG2P")
    wallet = req.wallet_address.strip() if req.wallet_address and req.wallet_address.strip() else default_fan_wallet

    users[username] = {
        "username": username,
        "password_hash": hashlib.sha256(req.password.encode()).hexdigest(),
        "wallet_address": wallet,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_users(users)

    return {
        "status": "success",
        "message": "Registrazione completata con successo!",
        "username": username,
        "wallet_address": wallet,
    }


@app.post("/api/auth/login")
def login_user(req: AuthRequest):
    username = req.username.strip()
    if not username or not req.password:
        raise HTTPException(status_code=400, detail="Inserisci sia username che password.")

    users = _load_users()
    matched_user = None
    for u, data in users.items():
        if u.lower() == username.lower():
            matched_user = data
            break

    if not matched_user:
        raise HTTPException(status_code=401, detail="Account non trovato. Clicca su 'Registrati' per crearne uno nuovo.")

    pwd_hash = hashlib.sha256(req.password.encode()).hexdigest()
    if matched_user["password_hash"] != pwd_hash:
        raise HTTPException(status_code=401, detail="Password errata. Riprova.")

    default_fan_wallet = os.getenv("FAN_ADDRESS", "rDrVhthSnhAv4YKUjskJ5v8KiQsQdeWG2P")
    return {
        "status": "success",
        "username": matched_user["username"],
        "wallet_address": matched_user.get("wallet_address", default_fan_wallet),
    }


# ==========================================================
# FAN ENDPOINTS
# ==========================================================

@app.get("/api/fan/connect")
def connect_fan(
    username: str = Query(default="guest"),
    n_artists: int = Query(default=8, ge=1, le=20),
):
    """
    Connects fan, checks Spotify eligibility, and claims/issues genuine
    XRPL Soulbound NFT Cards for each qualified artist.
    """
    streamed_artists = simulate_user_streams(username, n_artists=n_artists)
    is_top_vector = compute_top_listener_vector(username, streamed_artists)

    users = _load_users()
    matched_user = None
    for u, data in users.items():
        if u.lower() == username.lower():
            matched_user = data
            break

    default_fan_wallet = os.getenv("FAN_ADDRESS", "rDrVhthSnhAv4YKUjskJ5v8KiQsQdeWG2P")
    fan_wallet = matched_user.get("wallet_address", default_fan_wallet) if matched_user else default_fan_wallet

    current_cards = USER_CARDS_DB.get(username, [])
    # Sincronizza con il pool persistente per le carte già assegnate a questo utente
    pool = _load_pool()
    assigned_in_pool = [
        c for c in pool
        if c.get("assigned_to") == username and c.get("status") == "ASSIGNED"
    ]
    for c in assigned_in_pool:
        if not any(x["name"] == c.get("artist") for x in current_cards):
            artist_name = c.get("artist")
            current_cards.append({
                "name": artist_name,
                "percentage": c.get("percentage", 1.0),
                "streams": ARTISTS_DB.get(artist_name, {}).get("listeners_in_percentile", 1500),
                "pool_size": ARTISTS_DB.get(artist_name, {}).get("listeners_in_percentile", 2000),
                "nft_id": c.get("nft_id"),
                "explorer_url": c.get("explorer_url", "https://testnet.xrpscan.com"),
                "expiry_date": c.get("expiry_date", "2027-05-21T00:00:00"),
                "wallet": fan_wallet,
            })

    already_owned_artists = {c["name"] for c in current_cards}

    for entry, is_eligible in zip(streamed_artists, is_top_vector):
        if is_eligible:
            artist_name = entry["name"]
            pct = ARTISTS_DB[artist_name]["chosen_percentage"]

            if artist_name in already_owned_artists:
                continue

            # Assegna la carta dal pool SOLO se in stato AVAILABLE e l'utente non ne ha già usufruito
            card_data = claim_card_from_pool(
                artist_name=artist_name,
                fan_username=username,
                fan_address=fan_wallet,
            )

            if card_data:
                current_cards.append({
                    "name": artist_name,
                    "percentage": pct,
                    "streams": entry["streams"],
                    "pool_size": ARTISTS_DB[artist_name]["listeners_in_percentile"],
                    "nft_id": card_data["nft_id"],
                    "explorer_url": card_data.get("explorer_url", "https://testnet.xrpscan.com"),
                    "expiry_date": card_data.get("expiry_date", "2027-05-21T00:00:00"),
                    "wallet": fan_wallet,
                })
            else:
                print(f"[POOL] '{artist_name}': carta non assegnata (pool vuoto o già usufruita).")

    USER_CARDS_DB[username] = current_cards

    return {
        "username": username,
        "fan_wallet": fan_wallet,
        "streamed_artists": streamed_artists,
        "top_listener_vector": is_top_vector,
        "artists": USER_CARDS_DB[username],
    }


@app.post("/api/fan/redeem")
def redeem_card(req: RedeemRequest):
    """
    Redeems card perk at partner store and burns the NFT on-chain via XRPL.
    """
    cards = USER_CARDS_DB.get(req.username, [])
    card = next((c for c in cards if c["name"] == req.artist_name), None)

    if not card:
        raise HTTPException(status_code=404, detail="Card already used or not found")

    nft_id = card["nft_id"]
    fan_wallet = os.getenv("FAN_ADDRESS", "rLhwa8Wu7r2D1cr3nPenB5ndrcUA9LvCFL")

    # Real on-chain burn on XRPL Testnet
    burn_tx_hash = None
    try:
        burn_result = redeem_and_burn_card(
            fan_address=fan_wallet,
            nft_id=nft_id,
            vendor_id=req.perk_type,
        )
        if burn_result.get("success"):
            burn_tx_hash = burn_result.get("burn_tx_hash")
    except Exception as e:
        print(f"[WARN] XRPL Burn error (mock fallback if offline): {e}")

    # Mark as REDEEMED in pool registry
    pool = _load_pool()
    for c in pool:
        if c.get("nft_id") == nft_id:
            c["status"] = "REDEEMED"
            c["redeemed_vendor"] = req.perk_type
            c["burn_tx_hash"] = burn_tx_hash
            c["redeemed_at"] = datetime.now(timezone.utc).isoformat()
    _save_pool(pool)

    # Remove card from user's active collection
    USER_CARDS_DB[req.username] = [c for c in cards if c["name"] != req.artist_name]

    # Generate discount promo code
    prefix = "".join(ch for ch in req.artist_name if ch.isalnum()).upper()[:6] or "VIP"
    rand_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    code = (
        f"{prefix}-MERCH10-{rand_part}"
        if req.perk_type == "merch"
        else f"TM-{prefix}-{rand_part}"
    )

    return {
        "status": "success",
        "code": code,
        "burned_nft_id": nft_id,
        "burn_tx_hash": burn_tx_hash,
        "explorer_burn_url": f"https://testnet.xrpscan.com/tx/{burn_tx_hash}" if burn_tx_hash else None,
        "remaining_artists": USER_CARDS_DB[req.username],
    }


# ==========================================================
# ADMIN & POOL ENDPOINTS
# ==========================================================

@app.get("/api/admin/artists")
def get_admin_artists():
    """Returns Spotify artist database with configured percentages and listener metrics."""
    pool_status = get_pool_status()
    by_artist = pool_status["by_artist"]

    result = []
    for name, data in ARTISTS_DB.items():
        artist_pool = by_artist.get(name, {"total": 0, "available": 0, "assigned": 0, "redeemed": 0})
        result.append({
            "name": name,
            "chosen_percentage": data["chosen_percentage"],
            "listeners_in_percentile": data["listeners_in_percentile"],
            "pool_total": artist_pool["total"],
            "pool_available": artist_pool["available"],
            "pool_assigned": artist_pool["assigned"],
            "pool_redeemed": artist_pool["redeemed"],
        })
    return {"artists": result}


@app.get("/api/admin/pool/status")
def get_pool_metrics():
    """Returns the complete status of the pre-minted 6-month NFT card pool."""
    return get_pool_status()


@app.post("/api/admin/pool/generate")
def admin_generate_pool(req: PoolGenerateRequest):
    """
    Triggers 6-month batch minting of Soulbound NFTs for an artist on XRPL.
    """
    if req.artist_name not in ARTISTS_DB:
        raise HTTPException(status_code=400, detail=f"Artist '{req.artist_name}' not in Spotify database")

    try:
        result = generate_artist_pool(
            artist_name=req.artist_name,
            count=req.count,
            validity_days=180,
        )
        return result
    except Exception as e:
        print(f"[ERROR] generate_artist_pool error: {e}")
        raise HTTPException(status_code=500, detail=f"Minting error: {e}")


@app.get("/admin")
def serve_admin():
    """Serves the Admin Panel."""
    admin_path = ROOT_DIR / "frontend" / "admin.html"
    if admin_path.exists():
        return FileResponse(admin_path)
    return {"message": "Admin interface file not found"}


# Mount static frontend
app.mount("/", StaticFiles(directory=ROOT_DIR / "frontend", html=True), name="frontend")
