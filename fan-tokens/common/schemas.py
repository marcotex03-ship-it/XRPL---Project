"""CONTRATTI CONDIVISI: strutture dati scambiate tra i moduli.
Modificare solo dopo accordo tra i gruppi."""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

EventType = Literal["listen", "purchase", "concert", "social"]
Tier = Literal["none", "bronze", "silver", "gold"]


@dataclass
class ActivityEvent:
    user_id: int
    artist_id: int
    type: EventType
    value: float            # es. minuti ascoltati, euro spesi, 1 per un concerto
    occurred_at: datetime


@dataclass
class ScoreResult:
    user_id: int
    artist_id: int
    score: float
    tier: Tier
    eligible: bool          # ha superato la soglia per ricevere punti/carta


@dataclass
class MintResult:
    nft_id: str
    offer_id: str           # offerta a 0 XRP che il fan deve accettare


@dataclass
class Redemption:
    code: str
    user_id: int
    offer_id: int
    points_spent: int
