"""
mint_and_send.py
================
Module for minting non-transferable (Soulbound) Fan Card NFTs on the XRPL Testnet
and transferring them from the Platform wallet to the Fan's wallet.

Key XRPL Features Used:
- NFTokenMint with tfTransferable=False (Soulbound: non-transferable between fans).
- NFTokenMint with tfBurnable=True (Allows the platform/issuer to burn the card upon redemption).
- NFTokenCreateOffer (Zero-cost sell offer directed exclusively to the fan's address).
- NFTokenAcceptOffer (Fan claims the card into their wallet).
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Tuple
from dotenv import load_dotenv

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import (
    NFTokenMint,
    NFTokenMintFlag,
    NFTokenCreateOffer,
    NFTokenCreateOfferFlag,
    NFTokenAcceptOffer,
)
from xrpl.utils import str_to_hex, hex_to_str, get_nftoken_id

# Directory configuration
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

DEFAULT_TESTNET_URL = "https://s.altnet.rippletest.net:51234"


def get_client() -> JsonRpcClient:
    """Returns an active JsonRpcClient connected to the XRPL Testnet."""
    load_dotenv(dotenv_path=ENV_PATH)
    url = os.getenv("XRPL_TESTNET_URL", DEFAULT_TESTNET_URL)
    return JsonRpcClient(url)


DEFAULT_PLATFORM_SEED = "sEdSXHHzWrhvYfhxh6U1NNBxa4BkpGN"
DEFAULT_FAN_SEED = "sEd7fAUtpiDZMbFBmoKyv6noSd3AZxg"


def load_wallets() -> Tuple[Wallet, Wallet]:
    """Loads Platform and Fan wallets from the local .env file or default testnet seeds."""
    load_dotenv(dotenv_path=ENV_PATH)
    platform_seed = os.getenv("PLATFORM_SEED") or DEFAULT_PLATFORM_SEED
    fan_seed = os.getenv("FAN_SEED") or DEFAULT_FAN_SEED

    try:
        platform_wallet = Wallet.from_seed(platform_seed)
        fan_wallet = Wallet.from_seed(fan_seed)
        return platform_wallet, fan_wallet
    except Exception as e:
        print(f"[WARN] Error deriving wallets from seed: {e}. Generating fallback wallets.")
        return Wallet.create(), Wallet.create()


def build_metadata_uri(artist_name: str, tier: str, serial_number: int = 1) -> str:
    """
    Builds a JSON metadata URI representing the collectible Fan Card.
    In production, this would point to IPFS or a secure metadata server.
    """
    metadata = {
        "title": f"{artist_name} - Fan Card",
        "artist": artist_name,
        "tier": tier,
        "serial": serial_number,
        "issuer": "MusicFanPass Platform",
        "transferable": False,
        "burnable_on_redemption": True,
    }
    # Formatted as a lightweight metadata URI
    return f"https://api.musicfancard.io/metadata/{artist_name.lower().replace(' ', '_')}_{serial_number}.json"


def mint_soulbound_nft(
    client: JsonRpcClient,
    platform_wallet: Wallet,
    metadata_uri: str,
    taxon: int = 0,
) -> str:
    """
    Mints a non-transferable (Soulbound) NFT on XRPL.

    XRPL Flags:
    - We OMIT TF_TRANSFERABLE: The fan cannot trade or sell the card to other users.
    - We SET TF_BURNABLE: Allows the issuer or owner to burn (destroy) the token once
      redeemed for a vendor discount.
    """
    uri_hex = str_to_hex(metadata_uri)

    # Soulbound flag configuration: TF_BURNABLE only
    mint_tx = NFTokenMint(
        account=platform_wallet.classic_address,
        nftoken_taxon=taxon,
        flags=NFTokenMintFlag.TF_BURNABLE,
        uri=uri_hex,
    )

    print("\n[MINT] Submitting NFTokenMint transaction...")
    response = submit_and_wait(mint_tx, client, platform_wallet)
    result_code = response.result.get("meta", {}).get("TransactionResult", "")

    if result_code != "tesSUCCESS":
        raise RuntimeError(f"NFT Mint failed with result code: {result_code}")

    nft_id = get_nftoken_id(response.result["meta"])
    if not nft_id:
        raise RuntimeError("Failed to extract NFTokenID from transaction metadata.")

    print(f"[MINT] Success! NFTokenID: {nft_id}")
    print(f"[MINT] Explorer: https://testnet.xrpscan.com/nft/{nft_id}")
    return nft_id


def transfer_nft_to_fan(
    client: JsonRpcClient,
    platform_wallet: Wallet,
    fan_wallet: Wallet,
    nft_id: str,
) -> str:
    """
    Transfers the minted NFT from Platform wallet to Fan wallet using XRPL offers:
    1. Platform creates a zero-cost Sell Offer dedicated specifically to the Fan.
    2. Fan accepts the Sell Offer, moving the NFT into their wallet.
    """
    # Step 1: Create dedicated sell offer
    print("\n[TRANSFER 1/2] Creating zero-cost Sell Offer for the fan...")
    create_offer_tx = NFTokenCreateOffer(
        account=platform_wallet.classic_address,
        nftoken_id=nft_id,
        amount="0",  # Free transfer (0 drops)
        destination=fan_wallet.classic_address,  # Restricted to this specific fan
        flags=NFTokenCreateOfferFlag.TF_SELL_NFTOKEN,
    )

    offer_response = submit_and_wait(create_offer_tx, client, platform_wallet)
    offer_result = offer_response.result.get("meta", {}).get("TransactionResult", "")
    if offer_result != "tesSUCCESS":
        raise RuntimeError(f"CreateOffer failed with result: {offer_result}")

    # Extract the offer index
    offer_id = None
    for node in offer_response.result["meta"]["AffectedNodes"]:
        if "CreatedNode" in node and node["CreatedNode"]["LedgerEntryType"] == "NFTokenOffer":
            offer_id = node["CreatedNode"]["LedgerIndex"]
            break

    if not offer_id:
        raise RuntimeError("Could not find NFTokenOffer ID in transaction metadata.")

    print(f"[TRANSFER 1/2] Offer created successfully! Offer ID: {offer_id}")

    # Step 2: Fan accepts the offer
    print("\n[TRANSFER 2/2] Fan accepting the offer...")
    accept_offer_tx = NFTokenAcceptOffer(
        account=fan_wallet.classic_address,
        nftoken_sell_offer=offer_id,
    )

    accept_response = submit_and_wait(accept_offer_tx, client, fan_wallet)
    accept_result = accept_response.result.get("meta", {}).get("TransactionResult", "")
    if accept_result != "tesSUCCESS":
        raise RuntimeError(f"AcceptOffer failed with result: {accept_result}")

    print(f"[TRANSFER 2/2] Success! NFT {nft_id} is now owned by Fan: {fan_wallet.classic_address}")
    return nft_id


def mint_and_deliver_fan_card(
    artist_name: str,
    tier: str = "Top 1% Listener",
    serial_number: int = 1,
) -> Dict[str, Any]:
    """
    Complete end-to-end flow:
    1. Generates metadata for the Fan Card.
    2. Mints the Soulbound NFT on the Platform wallet.
    3. Delivers the NFT into the Fan's wallet.
    Returns transaction and token details.
    """
    client = get_client()
    platform_wallet, fan_wallet = load_wallets()

    metadata_uri = build_metadata_uri(artist_name, tier, serial_number)

    print("=" * 65)
    print("   XRPL TESTNET - MINT & DELIVER FAN CARD")
    print("=" * 65)
    print(f"Artist:         {artist_name}")
    print(f"Tier:           {tier}")
    print(f"Metadata URI:   {metadata_uri}")
    print(f"Issuer:         {platform_wallet.classic_address}")
    print(f"Recipient (Fan):{fan_wallet.classic_address}")

    # Mint Soulbound NFT
    nft_id = mint_soulbound_nft(client, platform_wallet, metadata_uri)

    # Deliver to Fan
    transfer_nft_to_fan(client, platform_wallet, fan_wallet, nft_id)

    print("\n" + "=" * 65)
    print("   FAN CARD DELIVERED SUCCESSFULLY!")
    print("=" * 65)
    print(f"NFT ID:   {nft_id}")
    print(f"Owner:    {fan_wallet.classic_address}")
    print(f"Explorer: https://testnet.xrpscan.com/nft/{nft_id}")
    print("=" * 65 + "\n")

    return {
        "status": "success",
        "nft_id": nft_id,
        "artist": artist_name,
        "tier": tier,
        "owner_address": fan_wallet.classic_address,
        "explorer_url": f"https://testnet.xrpscan.com/nft/{nft_id}",
    }


if __name__ == "__main__":
    # Test execution: Mint and deliver an Arctic Monkeys Top 1% card
    mint_and_deliver_fan_card(
        artist_name="Arctic Monkeys",
        tier="Top 1% Listener",
        serial_number=1,
    )
