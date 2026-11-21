import random
import string
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from simulator.simulate_spotify import (
    ARTISTS_DB,
    simulate_user_streams,
    compute_top_listener_vector,
)

# ==========================================================
# IMPORT DAL MODULO XRPL_LAYER (Squadra A)
# Sostituite con il nome reale del file e delle funzioni in xrpl_layer/
# ==========================================================
# from xrpl_layer import mint_card, burn_card

app = FastAPI(title="SuperFan - XRPL Hackathon")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stato in memoria per la demo: tiene traccia delle carte attive per utente
USER_CARDS_DB: dict[str, list[dict]] = {}


class RedeemRequest(BaseModel):
    username: str
    artist_name: str
    perk_type: str  # "merch" oppure "ticketmaster"


def xrpl_mint_wrapper(username: str, artist_name: str, percentage: float) -> str:
    """
    Collega qui la funzione di mint di xrpl_layer/.
    Restituisce l'NFTokenID (o un ID mock se non ancora collegato).
    """
    # ESEMPIO QUANDO COLLEGATE XRPL_LAYER:
    # result = mint_card(username=username, artist=artist_name, top_percentage=percentage)
    # return result["nft_id"]

    fake_hex = "".join(random.choices("0123456789ABCDEF", k=16))
    return f"NFT-{fake_hex}"


def xrpl_burn_wrapper(username: str, nft_id: str) -> bool:
    """
    Collega qui la funzione di burn di xrpl_layer/.
    """
    # ESEMPIO QUANDO COLLEGATE XRPL_LAYER:
    # burn_card(username=username, nft_id=nft_id)
    return True


@app.get("/api/fan/connect")
def connect_fan(
    username: str = Query(default="guest"),
    n_artists: int = Query(default=8, ge=1, le=20),
):
    streamed_artists = simulate_user_streams(username, n_artists=n_artists)
    is_top_vector = compute_top_listener_vector(username, streamed_artists)

    # Se l'utente non ha ancora caricato le carte in questa sessione, le creiamo
    if username not in USER_CARDS_DB:
        earned_cards = []
        for entry, is_eligible in zip(streamed_artists, is_top_vector):
            if is_eligible:
                artist_name = entry["name"]
                pct = ARTISTS_DB[artist_name]["chosen_percentage"]
                nft_id = xrpl_mint_wrapper(username, artist_name, pct)

                earned_cards.append({
                    "name": artist_name,
                    "percentage": pct,
                    "streams": entry["streams"],
                    "pool_size": ARTISTS_DB[artist_name]["listeners_in_percentile"],
                    "nft_id": nft_id,
                })
        USER_CARDS_DB[username] = earned_cards

    return {
        "username": username,
        "streamed_artists": streamed_artists,
        "top_listener_vector": is_top_vector,
        "artists": USER_CARDS_DB[username],
    }


@app.post("/api/fan/redeem")
def redeem_card(req: RedeemRequest):
    """
    Chiamato quando l'utente riscatta un premio dal popup:
    1. Verifica che l'utente possieda la carta
    2. Chiama il burn su XRPL
    3. Rimuove la carta dal wallet dell'utente e genera il codice sconto
    """
    cards = USER_CARDS_DB.get(req.username, [])
    card = next((c for c in cards if c["name"] == req.artist_name), None)

    if not card:
        raise HTTPException(status_code=404, detail="Card already used or not found")

    # Burn su XRPL
    xrpl_burn_wrapper(req.username, card["nft_id"])

    # Rimuove la carta usata dalla collezione dell'utente
    USER_CARDS_DB[req.username] = [c for c in cards if c["name"] != req.artist_name]

    # Genera il codice sconto
    prefix = "".join(ch for ch in req.artist_name if ch.isalnum()).upper()[:6] or "VIP"
    rand_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    code = (
        f"{prefix}-MERCH10-{rand_part}"
        if req.perk_type == "merch"
        else f"TM-{prefix}-{rand_part}"
    )

    return {
        "code": code,
        "burned_nft_id": card["nft_id"],
        "remaining_artists": USER_CARDS_DB[req.username],
    }


# Serve automaticamente frontend/index.html e 18821-removebg-preview.png su http://localhost:3000
# IMPORTANTE: questa riga deve restare SEMPRE in fondo al file, dopo tutti gli endpoint /api/...
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
