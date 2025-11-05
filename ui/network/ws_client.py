import socketio
import threading
from PyQt6.QtCore import QObject, pyqtSignal


class WSClientSignals(QObject):
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error = pyqtSignal(str)
    notification = pyqtSignal(object)


class WSClient(QObject):
    """Background Socket.IO client that emits Qt signals on events."""
    def __init__(self, ws_url, token=None, merchant_id=None, shop_codes=None):
        super().__init__()
        self.signals = WSClientSignals()
        self.ws_url = ws_url
        self.token = token
        self.merchant_id = merchant_id
        self.shop_codes = shop_codes
        self._sio = None
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            self._sio = socketio.Client(reconnection=True, logger=False, engineio_logger=False)

            @self._sio.event
            def connect():
                try:
                    self.signals.connected.emit()
                    payload = {}
                    if self.merchant_id:
                        payload['merchant_id'] = self.merchant_id
                    if self.shop_codes:
                        if isinstance(self.shop_codes, (list, tuple)):
                            payload['shop_codes'] = ','.join([str(s) for s in self.shop_codes])
                        else:
                            payload['shop_code'] = str(self.shop_codes)
                    if payload:
                        try:
                            self._sio.emit('join', payload)
                        except Exception:
                            pass
                except Exception as ex:
                    self.signals.error.emit(str(ex))

            @self._sio.event
            def connect_error(data):
                try:
                    self.signals.error.emit(f'Connect error: {data}')
                except Exception:
                    pass

            @self._sio.event
            def disconnect():
                try:
                    self.signals.disconnected.emit()
                except Exception:
                    pass

            @self._sio.on('notification')
            def on_notification(msg):
                try:
                    print(f"[WSClient Debug] Received notification from server: {msg}")
                    self.signals.notification.emit(msg)
                    print("[WSClient Debug] Notification emitted to GUI")
                except Exception as e:
                    print(f"[WSClient Error] Failed to handle notification: {e}")
                    import traceback
                    print(traceback.format_exc())

            connect_params = {}
            if self.token:
                connect_params['token'] = self.token
            if self.merchant_id:
                connect_params['merchant_id'] = self.merchant_id
            qs = '&'.join([f"{k}={v}" for k, v in connect_params.items()])
            url = self.ws_url
            if qs:
                url = f"{self.ws_url}?{qs}"

            self._sio.connect(url, transports=('websocket',), wait=True, wait_timeout=10)
            self._sio.wait()

        except Exception as e:
            try:
                self.signals.error.emit(str(e))
            except Exception:
                pass

    def stop(self):
        try:
            if self._sio:
                self._sio.disconnect()
        except Exception:
            pass