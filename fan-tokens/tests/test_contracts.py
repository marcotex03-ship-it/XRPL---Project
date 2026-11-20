"""Verifica che i mock rispettino i contratti. Eseguire con: pytest"""
from datetime import datetime, timedelta

from economy.economy import MockEconomyService
from scoring.scoring import MockScoringEngine, score_events
from common.schemas import ActivityEvent
from xrpl_layer.xrpl_service import MockXRPLService


def test_scoring_pure():
    ev = [ActivityEvent(1, 1, "concert", 3, datetime.utcnow())]
    assert score_events(ev, 1, 1).tier == "bronze"


def test_scoring_mock():
    assert MockScoringEngine().evaluate_fan(1, 1).eligible


def test_xrpl_mock():
    r = MockXRPLService().mint_card(1, "rFAKE", "rare", datetime.utcnow())
    assert r.nft_id and r.offer_id


def test_economy_fifo_and_expiry():
    e = MockEconomyService()
    now = datetime.utcnow()
    e.award_points(1, 1, 100, now + timedelta(days=10))
    e.award_points(1, 1, 100, now + timedelta(days=30))
    e.redeem(1, 1, 1, 100)           # consuma il lotto che scade prima
    assert e.expire_points(now + timedelta(days=20)) == 0
    assert e.get_balance(1, 1) == 100
