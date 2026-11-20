# Contratti tra i gruppi

Questi file sono il contratto: si modificano solo dopo accordo.
- `common/models.py`  schema DB
- `common/schemas.py` strutture dati scambiate
- Interfacce (Protocol): `xrpl_layer/xrpl_service.py`, `scoring/scoring.py`, `economy/economy.py`

## Gruppi
- A Blockchain -> `xrpl_layer/`  (sostituire MockXRPLService con RealXRPLService)
- B Dati e scoring -> `scoring/`, OAuth Spotify, `common/`
- C Economia e merchant -> `economy/`
- D Frontend e integrazione -> `web/`, `tests/`

## Regole
- Branch per gruppo, pull request con revisione
- Nessun seed/chiave nel repo (.env)
- Ogni gruppo sviluppa contro i mock degli altri (USE_MOCKS=true)
