"""GRUPPO C: ledger punti, scadenza FIFO, riscatti. Interfaccia + mock."""
import secrets
from datetime import datetime
from typing import Protocol

from common.schemas import Redemption


class EconomyService(Protocol):
    def award_points(self, user_id: int, artist_id: int, amount: int,
                     expires_at: datetime) -> None: ...
    def get_balance(self, user_id: int, artist_id: int) -> int: ...
    def redeem(self, user_id: int, offer_id: int, artist_id: int,
               cost: int) -> Redemption: ...
    def expire_points(self, now: datetime) -> int: ...


class MockEconomyService:
    """Ledger in memoria: lotti (user, artist, remaining, expires_at)."""

    def __init__(self):
        self.lots: list[dict] = []

    def award_points(self, user_id, artist_id, amount, expires_at):
        self.lots.append(dict(user=user_id, artist=artist_id,
                              remaining=amount, expires=expires_at))

    def get_balance(self, user_id, artist_id):
        return sum(l["remaining"] for l in self.lots
                   if l["user"] == user_id and l["artist"] == artist_id)

    def redeem(self, user_id, offer_id, artist_id, cost):
        if self.get_balance(user_id, artist_id) < cost:
            raise ValueError("Punti insufficienti")
        to_spend = cost
        # FIFO: si consumano prima i lotti che scadono prima
        for lot in sorted((l for l in self.lots
                           if l["user"] == user_id and l["artist"] == artist_id),
                          key=lambda l: l["expires"]):
            used = min(lot["remaining"], to_spend)
            lot["remaining"] -= used
            to_spend -= used
            if to_spend == 0:
                break
        return Redemption(secrets.token_hex(4).upper(), user_id, offer_id, cost)

    def expire_points(self, now):
        expired = 0
        for lot in self.lots:
            if lot["expires"] <= now and lot["remaining"] > 0:
                expired += lot["remaining"]
                lot["remaining"] = 0
        return expired
