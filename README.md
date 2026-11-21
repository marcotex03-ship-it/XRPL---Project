# XRPL---Project

Piattaforma basata su **FastAPI** e **XRP Ledger (XRPL)** per l'emissione, gestione e riscatto di card da collezione Soulbound NFT per i top fan musicali.

---

## 🚀 Guida all'avvio / How to Run

Segui questi passaggi per configurare ed eseguire il progetto in locale:

### 1. Creazione e attivazione dell'ambiente virtuale (Consigliato)

Prima di installare le librerie, è consigliato creare un ambiente virtuale isolato:

**Su macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Su Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

---

### 2. Installazione delle dipendenze
Installa tutte le librerie necessarie (FastAPI, Uvicorn, xrpl-py, python-dotenv):
```bash
pip install -r requirements.txt
```

---

### 3. Configurazione dei Wallet XRPL Testnet
Genera automaticamente i wallet di test gratuiti (Platform e Fan) finanziati tramite il Faucet ufficiale di XRP Ledger e crea il file locale `.env`:
```bash
python3 xrpl_layer/wallet_setup.py
```
> **Nota:** Se questo passaggio viene saltato, il backend utilizzerà automaticamente una modalità di fallback/simulazione per consentire la demo senza crash.

---

### 4. Avvio del server dell'applicazione
Avvia il server FastAPI con reload automatico:
```bash
python3 -m uvicorn main:app --reload --port 8000
```

Il server sarà attivo all'indirizzo `http://127.0.0.1:8000`.

---

### 5. Accesso all'applicazione nel Browser
FastAPI serve sia il backend API sia l'interfaccia frontend:

* 🎵 **App Utente / Fan (Spotify Experience)**: [http://localhost:8000](http://localhost:8000)
* ⚙️ **Pannello Amministratore / Pool XRPL**: [http://localhost:8000/admin](http://localhost:8000/admin)
* 📑 **Documentazione interattiva API (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

Per arrestare il server in qualsiasi momento, premi `Ctrl + C` nel terminale.

---

## 👥 Best Practices per il Team

* **Keep dependencies synced:** Whenever someone installs a new library (such as Flask, FastAPI, or Pandas), add it to `requirements.txt` so teammates can run `pip install -r requirements.txt` to stay in sync.
* **Keep branches small and focused:** Build one feature per branch and merge often (every day or two). Long-lived branches make merging much harder.
* **Agree on function inputs and outputs early:** Before splitting up, agree on what each module expects so all parts connect cleanly in `main.py`.
