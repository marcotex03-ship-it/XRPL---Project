"""GRUPPO B: motore di scoring off-chain. Interfaccia + versione mock."""
from datetime import datetime, timedelta
from typing import Iterable, Protocol

from common.schemas import ActivityEvent, ScoreResult


class ScoringEngine(Protocol):
    def evaluate_fan(self, user_id: int, artist_id: int) -> ScoreResult: ...


# Pesi di esempio: ogni artista potrà avere regole proprie
WEIGHTS = {"listen": 0.1, "purchase": 5.0, "concert": 20.0, "social": 0.5}


def score_events(events: Iterable[ActivityEvent], user_id: int, artist_id: int,
                 window_days: int = 180) -> ScoreResult:
    """Logica pura: testabile con eventi finti (CSV), senza DB né blockchain."""
    since = datetime.utcnow() - timedelta(days=window_days)
    score = sum(WEIGHTS.get(e.type, 0) * e.value
                for e in events
                if e.user_id == user_id and e.artist_id == artist_id
                and e.occurred_at >= since)
    tier = ("gold" if score >= 500 else "silver" if score >= 200
            else "bronze" if score >= 50 else "none")
    return ScoreResult(user_id, artist_id, score, tier, eligible=tier != "none")


class MockScoringEngine:
    def evaluate_fan(self, user_id, artist_id):
        return ScoreResult(user_id, artist_id, 250.0, "silver", True)
