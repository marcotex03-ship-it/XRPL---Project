"""CONTRATTO: schema del database (Gruppo B lo mantiene, tutti lo usano)."""
from datetime import datetime
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        JSON, String)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    wallets = relationship("Wallet", back_populates="user")


class Artist(Base):
    __tablename__ = "artists"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    spotify_id = Column(String, unique=True)
    xrpl_issuer_address = Column(String)       # indirizzo pubblico, MAI il seed


class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    address = Column(String, unique=True, nullable=False)
    verified = Column(Boolean, default=False)  # possesso verificato via firma
    user = relationship("User", back_populates="wallets")


class ActivityEvent(Base):
    """Dati grezzi: restano off-chain per privacy."""
    __tablename__ = "activity_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), index=True)
    type = Column(String, nullable=False)      # listen|purchase|concert|social
    value = Column(Float, default=1.0)
    occurred_at = Column(DateTime, nullable=False)
    source = Column(String)                    # spotify|bandcamp|manual
    meta = Column(JSON)


class ScoreSnapshot(Base):
    __tablename__ = "score_snapshots"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), index=True)
    score = Column(Float, nullable=False)
    tier = Column(String, nullable=False)
    eligible = Column(Boolean, default=False)
    computed_at = Column(DateTime, default=datetime.utcnow)


class Card(Base):
    """Carta NFT non trasferibile."""
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), index=True)
    nft_id = Column(String, unique=True)
    offer_id = Column(String)
    rarity = Column(String, nullable=False)    # common|rare|epic|legendary
    minted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    burned = Column(Boolean, default=False)


class PointLedger(Base):
    """Ledger punti a lotti. 'remaining' permette la scadenza FIFO."""
    __tablename__ = "point_ledger"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), index=True)
    delta = Column(Integer, nullable=False)    # + accredito, - spesa/scadenza
    remaining = Column(Integer, default=0)     # solo per i lotti positivi
    reason = Column(String)                    # earn|redeem|expire
    season = Column(String)                    # es. "2026-Q4"
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)


class Merchant(Base):
    __tablename__ = "merchants"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String)                  # shop|tickets|vinyl|studio...


class MerchantOffer(Base):
    __tablename__ = "merchant_offers"
    id = Column(Integer, primary_key=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"))
    artist_id = Column(Integer, ForeignKey("artists.id"))  # token accettato
    description = Column(String)
    points_cost = Column(Integer, nullable=False)
    discount_percent = Column(Float)
    active = Column(Boolean, default=True)


class Redemption(Base):
    __tablename__ = "redemptions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    offer_id = Column(Integer, ForeignKey("merchant_offers.id"))
    code = Column(String, unique=True)
    status = Column(String, default="pending")  # pending|validated|cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
