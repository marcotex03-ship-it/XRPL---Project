"""
wallet_setup.py
================
Modulo per la creazione e il finanziamento di wallet di test sulla Testnet XRPL.
Genera due wallet:
1. Piattaforma (Issuer/Minter): la nostra piattaforma che conia le Fan Card NFT.
2. Fan (Receiver): l'utente/ascoltatore che riceve la card.

I seed vengono salvati nel file locale .env (escluso da Git tramite .gitignore).
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl.models.requests import AccountInfo
from xrpl.utils import drops_to_xrp

# Percorso della root del progetto (dove risiede il file .env)
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

# URL di default del nodo Testnet XRPL
DEFAULT_TESTNET_URL = "https://s.altnet.rippletest.net:51234"


def get_client(testnet_url: str = None) -> JsonRpcClient:
    """Restituisce un client JsonRpc collegato alla Testnet XRPL."""
    url = testnet_url or os.getenv("XRPL_TESTNET_URL", DEFAULT_TESTNET_URL)
    return JsonRpcClient(url)


def get_account_balance(client: JsonRpcClient, address: str) -> str:
    """Recupera il saldo in XRP di un account dal ledger."""
    try:
        response = client.request(AccountInfo(account=address, ledger_index="validated"))
        balance_drops = response.result["account_data"]["Balance"]
        return f"{drops_to_xrp(balance_drops):.2f} XRP"
    except Exception as e:
        return "N/D (In attesa di validazione)"


def setup_wallets(force_recreate: bool = False):
    """
    Crea e finanzia tramite Faucet i wallet della Piattaforma e del Fan.
    Salva indirizzi e seed nel file .env.
    """
    load_dotenv(dotenv_path=ENV_PATH)
    client = get_client()

    print("=" * 65)
    print("   XRPL TESTNET - SETUP WALLET PIATTAFORMA E FAN")
    print("=" * 65)
    print(f"Connessione a: {client.url}")

    # Controllo se i wallet esistono già in .env
    platform_seed = os.getenv("PLATFORM_SEED")
    fan_seed = os.getenv("FAN_SEED")

    if platform_seed and fan_seed and not force_recreate:
        print("\n[INFO] Wallet gia' presenti nel file .env:")
        platform_wallet = Wallet.from_seed(platform_seed)
        fan_wallet = Wallet.from_seed(fan_seed)

        print(f"\n[1] WALLET PIATTAFORMA:")
        print(f"    Indirizzo: {platform_wallet.classic_address}")
        print(f"    Saldo:     {get_account_balance(client, platform_wallet.classic_address)}")
        print(f"    Explorer:  https://testnet.xrpscan.com/account/{platform_wallet.classic_address}")

        print(f"\n[2] WALLET FAN:")
        print(f"    Indirizzo: {fan_wallet.classic_address}")
        print(f"    Saldo:     {get_account_balance(client, fan_wallet.classic_address)}")
        print(f"    Explorer:  https://testnet.xrpscan.com/account/{fan_wallet.classic_address}")

        print("\n(Per forzare la ricreazione con nuovi fondi, usa setup_wallets(force_recreate=True))\n")
        return platform_wallet, fan_wallet

    print("\n[1/2] Richiesta al Faucet per il Wallet PIATTAFORMA...")
    platform_wallet = generate_faucet_wallet(client)
    print(f"      Creato con successo!")
    print(f"      Indirizzo: {platform_wallet.classic_address}")
    print(f"      Seed:      {platform_wallet.seed}")
    print(f"      Saldo:     {get_account_balance(client, platform_wallet.classic_address)}")
    print(f"      Explorer:  https://testnet.xrpscan.com/account/{platform_wallet.classic_address}")

    print("\n[2/2] Richiesta al Faucet per il Wallet FAN...")
    fan_wallet = generate_faucet_wallet(client)
    print(f"      Creato con successo!")
    print(f"      Indirizzo: {fan_wallet.classic_address}")
    print(f"      Seed:      {fan_wallet.seed}")
    print(f"      Saldo:     {get_account_balance(client, fan_wallet.classic_address)}")
    print(f"      Explorer:  https://testnet.xrpscan.com/account/{fan_wallet.classic_address}")

    # Scrittura nel file .env
    env_content = f"""# ==========================================================
# CONFIGURAZIONE XRPL TESTNET (GENERATO AUTOMATICAMENTE)
# ==========================================================
XRPL_TESTNET_URL={client.url}

# Wallet della Piattaforma (Issuer / Minter)
PLATFORM_ADDRESS={platform_wallet.classic_address}
PLATFORM_SEED={platform_wallet.seed}

# Wallet del Fan (Ricevente)
FAN_ADDRESS={fan_wallet.classic_address}
FAN_SEED={fan_wallet.seed}
"""
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(env_content)

    print("\n" + "=" * 65)
    print(f"[OK] Credenziali salvate con successo in: {ENV_PATH}")
    print("[ATTENZIONE] Il file .env e' protetto da .gitignore e NON verra' caricato su GitHub.")
    print("=" * 65 + "\n")

    return platform_wallet, fan_wallet


def load_platform_wallet() -> Wallet:
    """Carica il wallet della Piattaforma dalle variabili di ambiente."""
    load_dotenv(dotenv_path=ENV_PATH)
    seed = os.getenv("PLATFORM_SEED")
    if not seed:
        raise ValueError("PLATFORM_SEED non trovato in .env. Esegui prima wallet_setup.py.")
    return Wallet.from_seed(seed)


def load_fan_wallet() -> Wallet:
    """Carica il wallet del Fan dalle variabili di ambiente."""
    load_dotenv(dotenv_path=ENV_PATH)
    seed = os.getenv("FAN_SEED")
    if not seed:
        raise ValueError("FAN_SEED non trovato in .env. Esegui prima wallet_setup.py.")
    return Wallet.from_seed(seed)


if __name__ == "__main__":
    setup_wallets()
