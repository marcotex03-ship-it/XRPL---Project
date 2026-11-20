# Fan Tokens (XRPL Testnet)

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    pytest
    uvicorn web.main:app --reload

Vedi `docs/CONTRATTI.md` per la divisione in gruppi e le interfacce.
