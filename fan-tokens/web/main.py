"""GRUPPO D: API FastAPI. Parte con i mock: uvicorn web.main:app --reload"""
from datetime import datetime, timedelta

from fastapi import FastAPI

from economy.economy import MockEconomyService
from scoring.scoring import MockScoringEngine
from xrpl_layer.xrpl_service import get_xrpl_service

app = FastAPI(title="Fan Tokens")
xrpl = get_xrpl_service()
scoring = MockScoringEngine()
economy = MockEconomyService()


@app.get("/fans/{user_id}/artists/{artist_id}/profile")
def fan_profile(user_id: int, artist_id: int):
    return {"points": economy.get_balance(user_id, artist_id),
            "score": scoring.evaluate_fan(user_id, artist_id)}


@app.post("/fans/{user_id}/artists/{artist_id}/claim")
def claim(user_id: int, artist_id: int, fan_address: str):
    result = scoring.evaluate_fan(user_id, artist_id)
    if not result.eligible:
        return {"claimed": False, "reason": "soglia non raggiunta"}
    expires = datetime.utcnow() + timedelta(days=90)
    economy.award_points(user_id, artist_id, int(result.score), expires)
    card = xrpl.mint_card(artist_id, fan_address, result.tier, expires)
    return {"claimed": True, "tier": result.tier, "card": card}
