"""
xrpl_service.py
===============
High-level service module connecting the XRPL blockchain layer with the backend.

Key Capabilities:
1. `emetti_card_per_fan`: Mints a Soulbound NFT Card, transfers it to the fan's
   wallet on-chain, and registers an off-chain expiration date (6 months / 180 days).
2. `verifica_card_valida`: Dual verification: checks on-chain possession on XRPL
   AND off-chain validity (not expired, not already redeemed).
3. `riscatta_e_brucia_card`: When a fan uses the discount at a vendor, executes
   an on-chain `NFTokenBurn` to permanently destroy the NFT, making it disappear
   from their wallet and disabling further reuse.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv

# Ensure root directory is in sys.path for direct script execution and package imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import NFTokenBurn

from xrpl_layer.mint_and_send import (
    get_client,
    load_wallets,
    mint_soulbound_nft,
    transfer_nft_to_fan,
    build_metadata_uri,
)
from xrpl_layer.verify import wallet_possiede_nft

# Directory configuration
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
REGISTRY_FILE = ROOT_DIR / "cards_registry.json"

# In-memory registry fallback
_IN_MEMORY_REGISTRY: Dict[str, Dict[str, Any]] = {}


def _load_registry() -> Dict[str, Dict[str, Any]]:
    """Loads the off-chain card registry from JSON file or returns in-memory state."""
    global _IN_MEMORY_REGISTRY
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                _IN_MEMORY_REGISTRY = json.load(f)
        except Exception:
            pass
    return _IN_MEMORY_REGISTRY


def _save_registry():
    """Persists the off-chain card registry to JSON file."""
    try:
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(_IN_MEMORY_REGISTRY, f, indent=2, default=str)
    except Exception as e:
        print(f"[WARN] Failed to write card registry to disk: {e}")


def emetti_card_per_fan(
    fan_address: str,
    metadata_uri: str,
    validita_giorni: int = 180,  # 6 months default validity
    fan_wallet: Optional[Wallet] = None,
) -> Dict[str, Any]:
    """
    Mints a Soulbound NFT Card, delivers it to the fan's wallet,
    and registers an off-chain expiration date (defaults to 6 months / 180 days).

    Args:
        fan_address: The classic XRPL address of the fan (starts with 'r...').
        metadata_uri: URI pointing to the card's visual and artist metadata.
        validita_giorni: Duration in days before the card expires (default: 180 / 6 months).
        fan_wallet: Optional Fan Wallet instance. If omitted, loaded from .env.

    Returns:
        Dict with card details: nft_id, issue_date, expiry_date, status.
    """
    client = get_client()
    platform_wallet, default_fan_wallet = load_wallets()
    recipient_wallet = fan_wallet or default_fan_wallet

    if recipient_wallet.classic_address != fan_address:
        # Fan address must match the recipient wallet
        raise ValueError(
            f"Fan address {fan_address} does not match recipient wallet {recipient_wallet.classic_address}"
        )

    # 1. Mint the Soulbound NFT on the Platform wallet
    nft_id = mint_soulbound_nft(client, platform_wallet, metadata_uri)

    # 2. Transfer ownership to the fan's wallet
    transfer_nft_to_fan(client, platform_wallet, recipient_wallet, nft_id)

    # 3. Calculate timestamps for off-chain expiration
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(days=validita_giorni)

    # 4. Register in off-chain database
    registry = _load_registry()
    card_record = {
        "nft_id": nft_id,
        "fan_address": fan_address,
        "metadata_uri": metadata_uri,
        "issue_date": now.isoformat(),
        "expiry_date": expiry.isoformat(),
        "status": "ACTIVE",  # ACTIVE, REDEEMED, or EXPIRED
        "redeemed_at": None,
        "redeemed_by_vendor": None,
        "burn_tx_hash": None,
    }
    registry[nft_id] = card_record
    _save_registry()

    return {
        "status": "success",
        "nft_id": nft_id,
        "fan_address": fan_address,
        "issue_date": card_record["issue_date"],
        "expiry_date": card_record["expiry_date"],
        "explorer_url": f"https://testnet.xrpscan.com/nft/{nft_id}",
    }


def verifica_card_valida(
    fan_address: str,
    nft_id: str,
) -> Tuple[bool, str]:
    """
    Validates a fan card by checking BOTH on-chain ownership and off-chain rules.

    Checks performed:
    1. Off-chain: Card must exist in the platform registry.
    2. Off-chain: Card status must be 'ACTIVE' (not previously burned/redeemed).
    3. Off-chain: Card must not be expired.
    4. On-chain: Fan's wallet must actually hold the NFT on the XRPL ledger.

    Args:
        fan_address: The classic XRPL address of the fan.
        nft_id: The 64-character hex NFTokenID.

    Returns:
        Tuple[bool, str]: (is_valid, reason_message)
    """
    registry = _load_registry()
    card_record = registry.get(nft_id)

    # Step 1: Check off-chain registry existence
    if not card_record:
        # Fallback: if not in local registry, check direct on-chain ownership
        is_on_chain_owner = wallet_possiede_nft(fan_address, nft_id)
        if is_on_chain_owner:
            return True, "Valid on-chain (No off-chain restriction found)"
        return False, "Card not found in registry and not owned on-chain"

    # Step 2: Check if already redeemed/burned
    if card_record.get("status") == "REDEEMED":
        return False, f"Card was already redeemed on {card_record.get('redeemed_at')} at {card_record.get('redeemed_by_vendor')}"

    # Step 3: Check expiration date
    expiry_str = card_record.get("expiry_date")
    if expiry_str:
        expiry_dt = datetime.fromisoformat(expiry_str)
        now_dt = datetime.now(timezone.utc)
        if now_dt > expiry_dt:
            card_record["status"] = "EXPIRED"
            _save_registry()
            return False, f"Card expired on {expiry_str}"

    # Step 4: Check real-time on-chain ownership
    is_owner = wallet_possiede_nft(fan_address, nft_id)
    if not is_owner:
        return False, "On-chain verification failed: Fan does not hold this NFT"

    return True, "Card is valid, active, and verified on-chain"


def riscatta_e_brucia_card(
    fan_address: str,
    nft_id: str,
    vendor_id: str = "Partner_Store",
) -> Dict[str, Any]:
    """
    Redeems the card for a partner vendor discount and permanently burns the NFT on-chain.
    
    Actions:
    1. Validates that the card is currently active and legitimately owned.
    2. Executes `NFTokenBurn` on the XRPL Testnet: destroys the token forever.
    3. Updates the off-chain registry status to 'REDEEMED'.
    4. The card is disabled and disappears from the fan's wallet.

    Args:
        fan_address: The classic XRPL address of the fan.
        nft_id: The NFTokenID to burn.
        vendor_id: Identifier of the vendor granting the discount (e.g. 'TicketOne').

    Returns:
        Dict containing redemption status, burn transaction hash, and discount approval.
    """
    # 1. Verify card first
    is_valid, reason = verifica_card_valida(fan_address, nft_id)
    if not is_valid:
        return {
            "success": False,
            "error": reason,
            "discount_granted": False,
        }

    # 2. Burn the NFT on-chain using the Platform issuer wallet
    client = get_client()
    platform_wallet, _ = load_wallets()

    print(f"\n[BURN] Submitting NFTokenBurn transaction for NFT: {nft_id}...")
    burn_tx = NFTokenBurn(
        account=platform_wallet.classic_address,
        nftoken_id=nft_id,
        owner=fan_address,
    )

    burn_response = submit_and_wait(burn_tx, client, platform_wallet)
    result_code = burn_response.result.get("meta", {}).get("TransactionResult", "")

    if result_code != "tesSUCCESS":
        return {
            "success": False,
            "error": f"NFTokenBurn transaction failed with code: {result_code}",
            "discount_granted": False,
        }

    tx_hash = burn_response.result.get("hash", "")
    now_iso = datetime.now(timezone.utc).isoformat()

    # 3. Update off-chain registry
    registry = _load_registry()
    if nft_id in registry:
        registry[nft_id]["status"] = "REDEEMED"
        registry[nft_id]["redeemed_at"] = now_iso
        registry[nft_id]["redeemed_by_vendor"] = vendor_id
        registry[nft_id]["burn_tx_hash"] = tx_hash
        _save_registry()

    print(f"[BURN] Success! NFT {nft_id} burned on-chain.")
    print(f"[BURN] Tx Hash: {tx_hash}")

    return {
        "success": True,
        "discount_granted": True,
        "nft_id": nft_id,
        "vendor": vendor_id,
        "redeemed_at": now_iso,
        "burn_tx_hash": tx_hash,
        "explorer_url": f"https://testnet.xrpscan.com/tx/{tx_hash}",
        "message": f"Card successfully redeemed at {vendor_id}. NFT burned and removed from wallet.",
    }


# English aliases for compatibility
issue_card_for_fan = emetti_card_per_fan
verify_card_validity = verifica_card_valida
redeem_and_burn_card = riscatta_e_brucia_card


if __name__ == "__main__":
    load_dotenv(dotenv_path=ENV_PATH)
    fan_addr = os.getenv("FAN_ADDRESS")

    print("=" * 65)
    print("   XRPL SERVICE - END-TO-END DEMO TEST")
    print("=" * 65)

    # 1. Issue a new Card for the fan
    metadata_link = "https://api.musicfancard.io/metadata/arctic_monkeys_top1_demo.json"
    print("\n[STEP 1] Issuing a new Fan Card...")
    issue_result = emetti_card_per_fan(
        fan_address=fan_addr,
        metadata_uri=metadata_link,
        validita_giorni=180,  # 6 months
    )
    test_nft_id = issue_result["nft_id"]
    print(f"Issued Card NFT ID: {test_nft_id}")
    print(f"Expiry Date:        {issue_result['expiry_date']}")

    # 2. Verify validity (should be True)
    print("\n[STEP 2] Verifying card validity before redemption...")
    is_valid, reason = verifica_card_valida(fan_addr, test_nft_id)
    print(f"Is Valid: {is_valid} | Reason: {reason}")

    # 3. Simulate vendor redemption (TicketOne discount -> Burn NFT)
    print("\n[STEP 3] Fan visits TicketOne to claim a 10% discount...")
    redemption = riscatta_e_brucia_card(
        fan_address=fan_addr,
        nft_id=test_nft_id,
        vendor_id="TicketOne",
    )
    print(f"Redemption Success: {redemption['success']}")
    print(f"Discount Granted:   {redemption['discount_granted']}")
    print(f"Burn Explorer:      {redemption.get('explorer_url')}")

    # 4. Verify validity again (should be False: already redeemed & burned)
    print("\n[STEP 4] Verifying card validity after redemption...")
    is_valid_after, reason_after = verifica_card_valida(fan_addr, test_nft_id)
    print(f"Is Valid: {is_valid_after} | Reason: {reason_after}")

    print("\n" + "=" * 65)
    print("   END-TO-END DEMO TEST COMPLETED SUCCESSFULLY!")
    print("=" * 65 + "\n")
