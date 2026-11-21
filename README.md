# SuperFan - XRPL Soulbound Loyalty Platform

SuperFan is a decentralized loyalty and rewards platform built on the XRP Ledger (XRPL) that bridges streaming metrics with non-transferable digital collectibles. The platform identifies eligible top listeners on streaming services and issues genuine Soulbound (XLS-20) NFT passes on the XRPL Testnet. These passes unlock single-use perks, such as merchandise discounts and concert ticket presales, which permanently burn the NFT on-chain upon redemption to prevent duplicate usage.

---

## Technical Overview

- Backend Framework: FastAPI (Python 3.9+) with Uvicorn ASGI server.
- Blockchain Integration: XRP Ledger (XRPL Testnet) using the xrpl-py SDK (v5.2+).
- Token Standard: XRPL XLS-20 Native Non-Fungible Tokens.
  - tfTransferable is set to False: Tokens are strictly Soulbound and cannot be transferred or sold between wallets.
  - tfBurnable is set to True: The platform maintains authority to destroy the NFT on-chain upon perk redemption.
- Pool Architecture: Pre-minted administrative batches with a strict state machine:
  - AVAILABLE: Pre-minted by the administrator during 6-month cycles.
  - ASSIGNED: Claimed by a qualified listener upon login.
  - REDEEMED: Permanently burned on-chain via NFTokenBurn transaction upon reward redemption.

---

## Installation and Setup

### Prerequisites
- Python 3.9 or higher
- Git

### Step 1: Navigate to the Project Directory
```bash
cd XRPL---Project
```

### Step 2: Set Up Python Virtual Environment
On macOS and Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:
```powershell
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration (Optional)
The platform includes valid pre-configured XRPL Testnet wallets by default. To generate fresh Testnet wallets and fund them via the Ripple faucet, run:
```bash
python3 xrpl_layer/wallet_setup.py
```

### Step 5: Start the Server
```bash
python3 -m uvicorn main:app --reload --port 8000
```
The server will start at http://127.0.0.1:8000.

---

## Judge Demonstration Flow (Step-by-Step)

The demonstration consists of two interconnected interfaces: the Admin Panel (issuer side) and the Fan App (listener side).

### Part 1: Admin Panel (Pre-Minting Pool Cards)
1. Open your browser and navigate to:
   http://localhost:8000/admin
2. Review the artist listener database and pool metrics table.
3. Choose an artist (for example, "Queen" or "Arctic Monkeys") and click the "Pre-Mint 2 Cards" button.
4. The system mints XLS-20 Soulbound NFTs on XRPL and adds them to the pool registry with status AVAILABLE.
5. Verify that the table updates to show 2 available cards for that artist.

### Part 2: Fan Experience (Claiming and Using Passes)
1. Open a new browser tab and navigate to:
   http://localhost:8000
2. Log in using the default test account:
   - Username: isa
   - Password: bari
   (You can also click "Register" to create a new fan profile).
3. Click "Connect Spotify". The simulator calculates streaming metrics and checks if the user qualifies as a Top Fan.
4. If qualified artists have pre-minted cards in the pool, the system claims them and assigns them to the fan's wallet address.
5. In the Fan Dashboard, inspect the claimed VIP passes, displaying the artist photo, listener percentile, and unique NFT token identifier.
6. Click "Use your card" on any active pass.
7. Select a perk type (Merchandise Discount or Ticketmaster Presale) and click "Confirm Redemption".
8. The system executes an NFTokenBurn transaction on XRPL, permanently destroys the NFT, generates a verified single-use promo code, and removes the pass from active inventory.

### Part 3: API Documentation
The interactive OpenAPI/Swagger documentation is available at:
http://localhost:8000/docs
All endpoints for authentication, pool status, administrative minting, and fan redemptions can be tested directly from this interface.
