# M-Pesa Callback Notification Server

This Python application receives M-Pesa callbacks (both STK Push and direct till payments) and displays desktop notifications with the payment details.

## Features


## Requirements


## Setup

1. Install the required packages:
   ```bash
   pip install flask requests plyer python-dotenv
   ```

2. Configure your environment variables in the `.env` file:
   ```
   CONSUMER_KEY=your_consumer_key
   CONSUMER_SECRET=your_consumer_secret
   SHORTCODE=your_shortcode
   PASSKEY=your_passkey
   CALLBACK_URL=your_callback_url
   ```

3. Start ngrok to expose your local server:
   ```bash
   ngrok http 5000
   ```

4. Update your callback URLs in the M-Pesa developer portal with your ngrok URL:
   - STK Push callback: `https://your-ngrok-url/stk-callback`
   - C2B callback: `https://your-ngrok-url/c2b-callback`

5. Run the callback server:
   ```bash
   python app.py
   ```

6. Run the GUI application (in a separate terminal):
   ```bash
   python gui.py
   ```

## Usage

Once both applications are running:
1. The server will show a notification that it has started
2. Listen for callbacks on port 5000
3. Display desktop notifications whenever payments are received
4. Use the GUI to send STK push requests:
   - Enter the phone number (format: 254XXXXXXXXX)
   - Enter the amount in KES
   - Click "Send STK Push"
5. View transaction history in the GUI
6. Handle both successful and failed transactions

## Endpoints


## Notes

# M-Pesa Manager (GUI) and Server example

This repository contains a desktop GUI for merchants (`gui.py`) and a minimal server example (`server_ws_example.py`) that receives M-Pesa callbacks and forwards them to connected merchants via Socket.IO.

Overview

- `gui.py` — Tkinter GUI with pages to send STK pushes, register C2B URLs, and connect to a notification server.
- `server_ws_example.py` — Flask + Flask-SocketIO example that stores callbacks in SQLite and emits `notification` events to merchant rooms.

Requirements

- Python 3.8+
- See `requirements.txt` for the full list. Example packages: `requests`, `python-dotenv`, `python-socketio`, `flask`, `flask-socketio`, `eventlet`.

Quick start (Windows PowerShell)

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the server (for local testing):

```powershell
python server_ws_example.py
```

4. Run the GUI (in another terminal):

```powershell
python gui.py
```

Using the system

- In the GUI: Connect → enter server URL (e.g. `http://localhost:5000`) and Merchant ID → Connect.
- Use the GUI `Dashboard` page to send STK pushes (requires your M-Pesa sandbox credentials in `.env`).
- When the server receives a callback it will store it in `callbacks.db` and emit a `notification` event to the merchant room. Connected GUIs will show a popup and the transaction will appear in Transactions.

Testing callbacks manually

Use curl or PowerShell's Invoke-RestMethod to simulate callbacks:

```powershell
curl -X POST http://localhost:5000/stk-callback -H "Content-Type: application/json" -d '{"merchant_id":"merchantA","amount":1000,"phone":"2547...","txid":"MP123"}'
```

Files of interest

- `gui.py` — the desktop application
- `server_ws_example.py` — example server that persists callbacks and emits Socket.IO events
- `requirements.txt` — dependencies
- `callbacks.db` — SQLite DB created by the server (after first run)

Security & production notes

- This project is a demo. For production you must add proper authentication, TLS (HTTPS/WSS), input validation, rate limiting, logging, and run behind a production-ready WSGI server.
- Consider using JWTs and join rooms server-side for merchant-specific routing.

Next steps you can ask me to implement

- Improve server auth (JWT) and secure WebSocket auth
- Add transaction history UI synchronized from server
- Package the GUI as an installer for Windows

---
Small note: if you want I can further update the GUI to use a Socket.IO client that joins rooms explicitly and only receives notifications for the logged-in merchant.