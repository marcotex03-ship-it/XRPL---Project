"""
verify.py
=========
Module for verifying NFT Card ownership directly on the XRPL Testnet.

Domain Concept:
- A "Card" is an on-chain Soulbound NFT issued by the Platform.
- The artist is an external reference/attribute (e.g., Arctic Monkeys, Taylor Swift)
  who initially configured a fan percentage threshold, but does NOT interact with
  the blockchain.
- The Fan holds the Card in their XRPL wallet.
- Vendors and the Backend query this module to verify whether a fan's wallet
  legitimately owns a valid Card before issuing discounts.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountNFTs
from xrpl.utils import hex_to_str

# Directory configuration
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

DEFAULT_TESTNET_URL = "https://s.altnet.rippletest.net:51234"


def get_client(testnet_url: Optional[str] = None) -> JsonRpcClient:
    """Returns an active JsonRpcClient connected to the XRPL Testnet."""
    load_dotenv(dotenv_path=ENV_PATH)
    url = testnet_url or os.getenv("XRPL_TESTNET_URL", DEFAULT_TESTNET_URL)
    return JsonRpcClient(url)


def wallet_possiede_nft(
    wallet_address: str,
    nft_id: str,
    client: Optional[JsonRpcClient] = None,
) -> bool:
    """
    Checks whether a specific XRPL wallet currently owns a specific NFTokenID on-chain.

    Args:
        wallet_address: The classic XRPL address of the fan (starts with 'r...').
        nft_id: The 64-character hex NFTokenID to look for.
        client: Optional JsonRpcClient instance (creates one if not provided).

    Returns:
        bool: True if the wallet holds this NFT, False otherwise.
    """
    if not wallet_address or not nft_id:
        return False

    client = client or get_client()

    try:
        request = AccountNFTs(account=wallet_address)
        response = client.request(request)
        account_nfts = response.result.get("account_nfts", [])

        # Check if the requested NFTokenID is in the user's NFT page
        for nft in account_nfts:
            if nft.get("NFTokenID") == nft_id.strip():
                return True

        return False

    except Exception as e:
        print(f"[ERROR] Failed to query account NFTs for {wallet_address}: {e}")
        return False


# English alias for consistency
wallet_holds_nft = wallet_possiede_nft


def get_wallet_cards(
    wallet_address: str,
    client: Optional[JsonRpcClient] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves all NFT Cards currently held by a fan's wallet,
    decoding their URI metadata from hexadecimal.

    Args:
        wallet_address: The classic XRPL address of the fan.
        client: Optional JsonRpcClient instance.

    Returns:
        List of dicts containing NFTokenID, raw URI, decoded URI, and flags.
    """
    client = client or get_client()

    try:
        request = AccountNFTs(account=wallet_address)
        response = client.request(request)
        raw_nfts = response.result.get("account_nfts", [])

        cards = []
        for item in raw_nfts:
            raw_uri = item.get("URI", "")
            decoded_uri = hex_to_str(raw_uri) if raw_uri else "N/A"

            cards.append({
                "nft_id": item.get("NFTokenID"),
                "flags": item.get("Flags"),
                "issuer": item.get("Issuer"),
                "taxon": item.get("NFTokenTaxon"),
                "uri": decoded_uri,
            })

        return cards

    except Exception as e:
        print(f"[ERROR] Could not fetch cards for {wallet_address}: {e}")
        return []


if __name__ == "__main__":
    load_dotenv(dotenv_path=ENV_PATH)
    fan_address = os.getenv("FAN_ADDRESS")

    print("=" * 65)
    print("   XRPL TESTNET - NFT CARD OWNERSHIP VERIFIER")
    print("=" * 65)

    if not fan_address:
        print("[ERROR] FAN_ADDRESS not found in .env. Run wallet_setup.py first.")
        exit(1)

    print(f"Target Fan Wallet: {fan_address}")

    # 1. Fetch all cards in the fan's wallet
    fan_cards = get_wallet_cards(fan_address)
    print(f"\nTotal Cards Found in Fan Wallet: {len(fan_cards)}")

    for idx, card in enumerate(fan_cards, 1):
        print(f"  [{idx}] NFTokenID: {card['nft_id']}")
        print(f"      Metadata URI: {card['uri']}")
        print(f"      Explorer: https://testnet.xrpscan.com/nft/{card['nft_id']}")

    # 2. Test positive verification if we have at least one card
    if fan_cards:
        valid_nft_id = fan_cards[0]["nft_id"]
        is_owner = wallet_possiede_nft(fan_address, valid_nft_id)
        print(f"\n[TEST 1 - Positive Check]")
        print(f"  Verifying genuine NFT: {valid_nft_id}")
        print(f"  Result: {'OWNERSHIP CONFIRMED (True)' if is_owner else 'FAILED (False)'}")

    # 3. Test negative verification with a random dummy NFT ID
    fake_nft_id = "0001000000000000000000000000000000000000000000000000000000000000"
    is_fake_owner = wallet_possiede_nft(fan_address, fake_nft_id)
    print(f"\n[TEST 2 - Negative Check]")
    print(f"  Verifying fake NFT: {fake_nft_id}")
    print(f"  Result: {'REJECTED AS EXPECTED (False)' if not is_fake_owner else 'UNEXPECTED (True)'}")

    print("\n" + "=" * 65 + "\n")
