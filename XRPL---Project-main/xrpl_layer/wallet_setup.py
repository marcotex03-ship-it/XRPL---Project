"""
wallet_setup.py
================
Module for creating and funding test wallets on the XRPL Testnet.
Generates two distinct wallets:
1. Platform Wallet (Issuer/Minter): Our platform entity that mints Fan Card NFTs.
2. Fan Wallet (Receiver): The fan/listener who receives the card.

Seeds and addresses are safely stored in a local .env file (excluded from Git via .gitignore).
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl.models.requests import AccountInfo
from xrpl.utils import drops_to_xrp

# Root directory of the repository (where .env resides)
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

# Default XRPL Testnet JSON-RPC node
DEFAULT_TESTNET_URL = "https://s.altnet.rippletest.net:51234"


def get_client(testnet_url: str = None) -> JsonRpcClient:
    """Returns a JsonRpcClient connected to the XRPL Testnet."""
    url = testnet_url or os.getenv("XRPL_TESTNET_URL", DEFAULT_TESTNET_URL)
    return JsonRpcClient(url)


def get_account_balance(client: JsonRpcClient, address: str) -> str:
    """Fetches the XRP balance of an account from the validated ledger."""
    try:
        response = client.request(AccountInfo(account=address, ledger_index="validated"))
        balance_drops = response.result["account_data"]["Balance"]
        return f"{drops_to_xrp(balance_drops):.2f} XRP"
    except Exception:
        return "N/A (Pending validation)"


def setup_wallets(force_recreate: bool = False):
    """
    Creates and funds Platform and Fan wallets via Testnet Faucet.
    Saves addresses and seeds into the local .env file.
    """
    load_dotenv(dotenv_path=ENV_PATH)
    client = get_client()

    print("=" * 65)
    print("   XRPL TESTNET - PLATFORM & FAN WALLET SETUP")
    print("=" * 65)
    print(f"Connecting to: {client.url}")

    # Check if wallets already exist in .env
    platform_seed = os.getenv("PLATFORM_SEED")
    fan_seed = os.getenv("FAN_SEED")

    if platform_seed and fan_seed and not force_recreate:
        print("\n[INFO] Wallets already present in .env:")
        platform_wallet = Wallet.from_seed(platform_seed)
        fan_wallet = Wallet.from_seed(fan_seed)

        print(f"\n[1] PLATFORM WALLET (Issuer/Minter):")
        print(f"    Address:  {platform_wallet.classic_address}")
        print(f"    Balance:  {get_account_balance(client, platform_wallet.classic_address)}")
        print(f"    Explorer: https://testnet.xrpscan.com/account/{platform_wallet.classic_address}")

        print(f"\n[2] FAN WALLET (Receiver/User):")
        print(f"    Address:  {fan_wallet.classic_address}")
        print(f"    Balance:  {get_account_balance(client, fan_wallet.classic_address)}")
        print(f"    Explorer: https://testnet.xrpscan.com/account/{fan_wallet.classic_address}")

        print("\n(To force recreation with new faucet funds, pass force_recreate=True)\n")
        return platform_wallet, fan_wallet

    print("\n[1/2] Requesting faucet funding for PLATFORM WALLET...")
    platform_wallet = generate_faucet_wallet(client)
    print("      Created successfully!")
    print(f"      Address:  {platform_wallet.classic_address}")
    print(f"      Seed:     {platform_wallet.seed}")
    print(f"      Balance:  {get_account_balance(client, platform_wallet.classic_address)}")
    print(f"      Explorer: https://testnet.xrpscan.com/account/{platform_wallet.classic_address}")

    print("\n[2/2] Requesting faucet funding for FAN WALLET...")
    fan_wallet = generate_faucet_wallet(client)
    print("      Created successfully!")
    print(f"      Address:  {fan_wallet.classic_address}")
    print(f"      Seed:     {fan_wallet.seed}")
    print(f"      Balance:  {get_account_balance(client, fan_wallet.classic_address)}")
    print(f"      Explorer: https://testnet.xrpscan.com/account/{fan_wallet.classic_address}")

    # Write to local .env file
    env_content = f"""# ==========================================================
# XRPL TESTNET CONFIGURATION (AUTOMATICALLY GENERATED)
# ==========================================================
XRPL_TESTNET_URL={client.url}

# Platform Wallet (Issuer / Minter)
PLATFORM_ADDRESS={platform_wallet.classic_address}
PLATFORM_SEED={platform_wallet.seed}

# Fan Wallet (Receiver / User)
FAN_ADDRESS={fan_wallet.classic_address}
FAN_SEED={fan_wallet.seed}
"""
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(env_content)

    print("\n" + "=" * 65)
    print(f"[OK] Credentials saved successfully to: {ENV_PATH}")
    print("[SECURITY] .env is protected by .gitignore and will NEVER be pushed to GitHub.")
    print("=" * 65 + "\n")

    return platform_wallet, fan_wallet


def load_platform_wallet() -> Wallet:
    """Loads the Platform wallet from environment variables."""
    load_dotenv(dotenv_path=ENV_PATH)
    seed = os.getenv("PLATFORM_SEED")
    if not seed:
        raise ValueError("PLATFORM_SEED not found in .env. Run wallet_setup.py first.")
    return Wallet.from_seed(seed)


def load_fan_wallet() -> Wallet:
    """Loads the Fan wallet from environment variables."""
    load_dotenv(dotenv_path=ENV_PATH)
    seed = os.getenv("FAN_SEED")
    if not seed:
        raise ValueError("FAN_SEED not found in .env. Run wallet_setup.py first.")
    return Wallet.from_seed(seed)


if __name__ == "__main__":
    setup_wallets()
