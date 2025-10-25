"""
Minimal Flask + Flask-SocketIO example to receive M-Pesa callbacks and broadcast
notifications to connected merchant clients.

Usage:
    pip install -r requirements.txt
    python server_ws_example.py

This example exposes:
 - /stk-callback  (POST) - STK push callbacks
 - /c2b-callback  (POST) - C2B callbacks
 - Socket.IO endpoint at /socket.io/ for real-time notifications

Security: This example is minimal and not production-ready. Add auth and HTTPS before
using publicly.
"""
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv
import os
import sqlite3
from itsdangerous import URLSafeSerializer
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'callbacks.db')

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
socketio = SocketIO(app, cors_allowed_origins='*', logger=True, engineio_logger=True)

# Serializer for simple token generation (do NOT use as a full auth solution in prod)
serializer = URLSafeSerializer(app.config['SECRET_KEY'])


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS callbacks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        merchant_id TEXT,
        type TEXT,
        payload TEXT,
        created_at TEXT
    )
    ''')
    conn.commit()
    conn.close()


init_db()

# Simple mapping from merchant_id -> connected sockets (managed by rooms)
# Clients should join a room named after their merchant_id after connecting.

@app.route('/stk-callback', methods=['POST'])
def stk_callback():
    data = request.get_json(force=True)
    # Persist callback
    merchant = data.get('merchant_id') or data.get('BusinessShortCode') or data.get('ShortCode')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO callbacks (merchant_id, type, payload, created_at) VALUES (?, ?, ?, ?)',
              (merchant, 'stk', str(data), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

    # Emit to merchant room if merchant id known, otherwise to all rooms
    try:
        # Try to get merchant ID from metadata first (our new field)
        metadata = data.get('Metadata', {})
        if isinstance(metadata, dict):
            merchant = metadata.get('merchant_id') or merchant

        # Extract merchant from Body.stkCallback if present
        try:
            body = data.get('Body', {}).get('stkCallback', {})
            if body:
                merchant = merchant or body.get('BusinessShortCode')
        except Exception:
            pass

        if merchant:
            print(f"[{datetime.now().isoformat()}] Emitting STK notification to merchant room: {merchant}")
            socketio.emit('notification', {'type': 'transaction', 'data': data}, room=merchant)
        else:
            print(f"[{datetime.now().isoformat()}] Broadcasting STK notification (no merchant found in data)")
            socketio.emit('notification', {'type': 'transaction', 'data': data}, to=None)  # to=None means all clients
    except Exception as e:
        print(f"Error emitting notification: {e}")
    return jsonify({'status': 'ok'})

@app.route('/c2b-callback', methods=['POST'])
def c2b_callback():
    data = request.get_json(force=True)
    merchant = data.get('merchant_id') or data.get('BusinessShortCode') or data.get('ShortCode')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO callbacks (merchant_id, type, payload, created_at) VALUES (?, ?, ?, ?)',
              (merchant, 'c2b', str(data), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

    try:
        if merchant:
            print(f"[{datetime.now().isoformat()}] Emitting C2B notification to merchant room: {merchant}")
            socketio.emit('notification', {'type': 'transaction', 'data': data}, room=merchant)
        else:
            print(f"[{datetime.now().isoformat()}] Broadcasting C2B notification (no merchant)")
            socketio.emit('notification', {'type': 'transaction', 'data': data}, to=None)  # to=None means all clients
    except Exception as e:
        print(f"Error emitting notification: {e}")
    return jsonify({'status': 'ok'})


@app.route('/api/login', methods=['POST'])
def api_login():
    j = request.get_json(force=True)
    username = j.get('username')
    password = j.get('password')
    # In a real app validate username/password against database
    if not username:
        return jsonify({'error': 'username required'}), 400

    # Issue a simple token that encodes merchant id
    token = serializer.dumps({'merchant_id': username})
    return jsonify({'token': token, 'merchant_id': username})

@socketio.on('connect')
def on_connect():
    # More informative connection logging
    try:
        sid = request.sid
    except Exception:
        sid = 'unknown'
    addr = request.remote_addr if hasattr(request, 'remote_addr') else 'unknown'
    now = datetime.utcnow().isoformat()
    # Print query params to help debug merchant_id passing
    try:
        args = request.args.to_dict()
    except Exception:
        args = {}
    print(f"[{now}] Client connected: sid={sid} addr={addr} args={args}")

    # If merchant_id passed as query param, auto-join that room
    try:
        merchant_q = request.args.get('merchant_id')
        if merchant_q:
            join_room(merchant_q)
            print(f"[{now}] sid={sid} joined room {merchant_q} (from query param)")
    except Exception:
        pass

@socketio.on('join')
def on_join(data):
    merchant = data.get('merchant_id')
    if merchant:
        join_room(merchant)
        emit('joined', {'room': merchant})
        try:
            sid = request.sid
        except Exception:
            sid = 'unknown'
        now = datetime.utcnow().isoformat()
        print(f"[{now}] sid={sid} joined room {merchant} via join event")

@socketio.on('disconnect')
def on_disconnect():
    try:
        sid = request.sid
    except Exception:
        sid = 'unknown'
    now = datetime.utcnow().isoformat()
    print(f"[{now}] Client disconnected: sid={sid}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
