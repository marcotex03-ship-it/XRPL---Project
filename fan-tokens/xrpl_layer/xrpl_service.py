"""GRUPPO A: layer XRPL. Interfaccia + implementazione reale + mock."""
import json
import os
import uuid
from datetime import datetime
from typing import Protocol

from common.schemas import MintResult


class XRPLService(Protocol):
    def mint_card(self, artist_id: int, fan_address: str, rarity: str,
                  expires_at: datetime) -> MintResult: ...
    def accept_card(self, fan_seed: str, offer_id: str) -> bool: ...
    def burn_card(self, artist_id: int, nft_id: str, owner: str) -> bool: ...


class MockXRPLService:
    """Per i gruppi B, C, D: nessuna rete necessaria."""
    def mint_card(self, artist_id, fan_address, rarity, expires_at):
        return MintResult(nft_id="MOCK" + uuid.uuid4().hex.upper(),
                          offer_id="MOCKOFFER" + uuid.uuid4().hex.upper())

    def accept_card(self, fan_seed, offer_id):
        return True

    def burn_card(self, artist_id, nft_id, owner):
        return True


class RealXRPLService:
    """Implementazione su Testnet. Seed issuer da env: ISSUER_SEED_<artist_id>."""

    def __init__(self, rpc_url: str | None = None):
        from xrpl.clients import JsonRpcClient
        self.client = JsonRpcClient(
            rpc_url or os.getenv("XRPL_RPC_URL",
                                 "https://s.altnet.rippletest.net:51234"))
        self._issuers = {}

    def _issuer(self, artist_id: int):
        from xrpl.wallet import Wallet, generate_faucet_wallet
        if artist_id not in self._issuers:
            seed = os.getenv(f"ISSUER_SEED_{artist_id}")
            self._issuers[artist_id] = (Wallet.from_seed(seed) if seed
                                        else generate_faucet_wallet(self.client))
        return self._issuers[artist_id]

    def mint_card(self, artist_id, fan_address, rarity, expires_at):
        from xrpl.models.transactions import (NFTokenCreateOffer,
                                              NFTokenCreateOfferFlag,
                                              NFTokenMint, NFTokenMintFlag)
        from xrpl.transaction import submit_and_wait
        from xrpl.utils import get_nftoken_id, str_to_hex

        issuer = self._issuer(artist_id)
        # URI breve: in produzione punta a un JSON su IPFS o sul tuo server
        uri = f"https://example.org/cards/{artist_id}/{rarity}/{expires_at.date()}.json"
        mint = NFTokenMint(
            account=issuer.address,
            nftoken_taxon=1,
            uri=str_to_hex(uri),
            flags=NFTokenMintFlag.TF_BURNABLE,  # niente TF_TRANSFERABLE
        )
        res = submit_and_wait(mint, self.client, issuer).result
        nft_id = get_nftoken_id(res["meta"])

        offer = NFTokenCreateOffer(
            account=issuer.address,
            nftoken_id=nft_id,
            amount="0",
            destination=fan_address,
            flags=NFTokenCreateOfferFlag.TF_SELL_NFTOKEN,
        )
        res = submit_and_wait(offer, self.client, issuer).result
        offer_id = next(
            n["CreatedNode"]["LedgerIndex"]
            for n in res["meta"]["AffectedNodes"]
            if n.get("CreatedNode", {}).get("LedgerEntryType") == "NFTokenOffer")
        return MintResult(nft_id=nft_id, offer_id=offer_id)

    def accept_card(self, fan_seed, offer_id):
        """Solo Testnet: in produzione il fan firma con Xaman/Crossmark."""
        from xrpl.models.transactions import NFTokenAcceptOffer
        from xrpl.transaction import submit_and_wait
        from xrpl.wallet import Wallet
        fan = Wallet.from_seed(fan_seed)
        tx = NFTokenAcceptOffer(account=fan.address, nftoken_sell_offer=offer_id)
        res = submit_and_wait(tx, self.client, fan).result
        return res["meta"]["TransactionResult"] == "tesSUCCESS"

    def burn_card(self, artist_id, nft_id, owner):
        from xrpl.models.transactions import NFTokenBurn
        from xrpl.transaction import submit_and_wait
        issuer = self._issuer(artist_id)
        tx = NFTokenBurn(account=issuer.address, nftoken_id=nft_id, owner=owner)
        res = submit_and_wait(tx, self.client, issuer).result
        return res["meta"]["TransactionResult"] == "tesSUCCESS"


def get_xrpl_service() -> XRPLService:
    if os.getenv("USE_MOCKS", "true").lower() == "true":
        return MockXRPLService()
    return RealXRPLService()
