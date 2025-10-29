import tkinter as tk
import threading
from datetime import datetime
import os
import socketio
import sys
import ctypes
from tkinter import messagebox

try:
    from plyer import notification as plyer_notification
except ImportError:
    plyer_notification = None

from gui import (
    Dashboard, Transactions, Settings, LoginPage, Sidebar,
    LIGHT, PRIMARY
)
import mpesa_client
from config import SERVER_URL, WEBSOCKET_URL, LOGIN_URL

class MpesaManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("M-Pesa Manager")
        self.geometry("1400x900")
        self.configure(bg=LIGHT)
        
        # Create UI
        self.sidebar = Sidebar(self, self.switch_page)
        self.create_pages()
        self.switch_page("dashboard")
        
        # Focus on phone entry
        self.after(100, lambda: self.pages["dashboard"].phone_entry.focus())
    
    def create_pages(self):
        main_frame = tk.Frame(self, bg=LIGHT)
        main_frame.pack(fill="both", expand=True, padx=(10, 20), pady=20)
        
        self.pages = {
            "dashboard": Dashboard(main_frame, self.send_stk_push),
            "transactions": Transactions(main_frame),
            "connect": LoginPage(main_frame, self),
            "settings": Settings(main_frame)
        }
    
    def switch_page(self, page_name):
        # Hide all pages
        for page in self.pages.values():
            page.pack_forget()
        
        # Show selected page
        self.pages[page_name].pack(fill="both", expand=True)
        
        # If transactions page, refresh from server
        try:
            if page_name == 'transactions':
                tx_page = self.pages.get('transactions')
                server_base = getattr(self, '_server_url', None) or SERVER_URL
                if tx_page and server_base:
                    tx_page.load_from_server(server_base, limit=200)
        except Exception:
            pass
        
        # Update sidebar highlight
        for key, btn in self.sidebar.buttons.items():
            if key == page_name:
                btn.config(bg=PRIMARY)
            else:
                btn.config(bg=self.sidebar["bg"])
    
    def send_stk_push(self, phone, amount):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Get current merchant_id if logged in
        merchant_id = getattr(self, '_current_merchant_id', None)
        # Get current shop shortcode to use as PartyB (may be list)
        shop_codes = getattr(self, '_current_shop_codes', None)
        shortcode_to_use = None
        try:
            if isinstance(shop_codes, (list, tuple)) and len(shop_codes) > 0:
                shortcode_to_use = str(shop_codes[0])
            elif shop_codes is not None:
                shortcode_to_use = str(shop_codes)
        except Exception:
            shortcode_to_use = None

        # Add quick log entry
        try:
            log_path = os.path.join(os.path.dirname(__file__), 'stk_debug.log')
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"\n[{datetime.utcnow().isoformat()}] Send STK clicked - phone={phone} amount={amount} merchant={merchant_id}\n")
        except Exception:
            pass

        def worker():
            try:
                # Use shop shortcode if available
                if shortcode_to_use:
                    resp = mpesa_client.lipa_na_mpesa_online(phone, int(amount), 
                                                           merchant_id=merchant_id,
                                                           shortcode=shortcode_to_use)
                else:
                    resp = mpesa_client.lipa_na_mpesa_online(phone, int(amount),
                                                           merchant_id=merchant_id)

                # Log request/response
                try:
                    log_path = os.path.join(os.path.dirname(__file__), 'stk_debug.log')
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write('\n--- STK PUSH RUN ' + datetime.utcnow().isoformat() + ' ---\n')
                        try:
                            req = resp.request
                            f.write('STK REQUEST URL: ' + str(getattr(req, 'url', '')) + '\n')
                            f.write('STK REQ HEADERS: ' + str(getattr(req, 'headers', {})) + '\n')
                            body = getattr(req, 'body', '')
                            if isinstance(body, bytes):
                                try:
                                    body = body.decode('utf-8')
                                except Exception:
                                    body = str(body)
                            f.write('STK REQ BODY: ' + str(body) + '\n')
                        except Exception:
                            pass
                        f.write('STK STATUS: ' + str(getattr(resp, 'status_code', '')) + '\n')
                        f.write('STK RESPONSE TEXT:\n' + getattr(resp, 'text', '') + '\n')
                except Exception:
                    pass

                # Process response
                data = None
                try:
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as ex:
                    try:
                        j = resp.json()
                        err_code = j.get('errorCode') or j.get('error_code') or j.get('error')
                        err_msg = j.get('errorMessage') or j.get('error_message') or j.get('message')
                        if err_code or err_msg:
                            raise RuntimeError(f'STK error from provider: {err_code} - {err_msg}')
                    except Exception:
                        pass
                    raise RuntimeError(f'STK request failed: {ex} - response: {getattr(resp, "text", "")}')

                def on_success():
                    dash = self.pages.get('dashboard')
                    if dash:
                        dash.add_history(f"STK Push initiated: {phone} KES {amount} — {data.get('CheckoutRequestID') or data}")
                    messagebox.showinfo('STK Push', f"Request sent. Response: {data.get('ResponseDescription') or data}")
                self.after(0, on_success)

            except Exception as e:
                err = str(e)
                def on_error(err=err):
                    dash = self.pages.get('dashboard')
                    if dash:
                        dash.add_history(f"STK Push error: {err}")
                    messagebox.showerror('STK Push Error', err)
                self.after(0, on_error)

        threading.Thread(target=worker, daemon=True).start()

    def start_ws_client(self, ws_url, token=None, merchant_id=None, shop_codes=None):
        """Start WebSocket client for notifications"""
        try:
            import socketio
        except Exception:
            messagebox.showerror('Missing Dependency', 'python-socketio is required')
            return

        # Clean up existing client
        try:
            if hasattr(self, '_sio') and self._sio:
                try:
                    self._sio.disconnect()
                except Exception:
                    pass
        except Exception:
            pass

        # Configure Socket.IO client
        self._sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=1,
            reconnection_delay_max=5,
            logger=True,
            engineio_logger=True
        )

        @self._sio.event
        def connect():
            try:
                if hasattr(self, 'status_label'):
                    self.after(0, lambda: self.status_label.config(text='Connected to notification server'))
            except Exception:
                pass
            try:
                payload = {}
                if merchant_id:
                    payload['merchant_id'] = merchant_id
                    self._current_merchant_id = merchant_id
                if shop_codes:
                    if isinstance(shop_codes, (list, tuple)):
                        payload['shop_codes'] = ','.join([str(s) for s in shop_codes])
                    else:
                        payload['shop_code'] = str(shop_codes)
                    try:
                        self._current_shop_codes = shop_codes
                    except Exception:
                        pass
                if payload:
                    self._sio.emit('join', payload)
            except Exception:
                pass

        @self._sio.event
        def connect_error(data):
            try:
                if hasattr(self, 'status_label'):
                    self.after(0, lambda: self.status_label.config(text=f'WS connect error'))
                self.after(0, lambda: messagebox.showerror('WS Connect Error', f'Failed to connect to {ws_url}: {data}'))
            except Exception:
                pass

        @self._sio.event
        def disconnect():
            self._current_merchant_id = None
            try:
                if hasattr(self, 'status_label'):
                    self.after(0, lambda: self.status_label.config(text='Disconnected'))
            except Exception:
                pass

        @self._sio.on('notification')
        def on_notification(msg):
            try:
                # Normalize payload
                if isinstance(msg, list):
                    for it in msg:
                        if isinstance(it, dict):
                            msg = it
                            break

                if isinstance(msg, dict) and 'type' in msg:
                    d = msg.get('data', {}) or {}

                    # Filter by shop code
                    try:
                        notification_shop = None
                        if isinstance(d, dict):
                            notification_shop = d.get('BusinessShortCode') or d.get('ShortCode') or d.get('Shortcode')
                        if not notification_shop and isinstance(msg.get('data'), dict):
                            notification_shop = msg.get('data').get('BusinessShortCode') or msg.get('data').get('ShortCode')

                        if hasattr(self, '_current_shop_codes') and self._current_shop_codes and notification_shop:
                            try:
                                codes = [str(x) for x in self._current_shop_codes] if isinstance(self._current_shop_codes, (list, tuple)) else [str(self._current_shop_codes)]
                            except Exception:
                                codes = [str(self._current_shop_codes)]
                            if str(notification_shop) not in codes:
                                return
                    except Exception:
                        pass

                    # Process notification
                    ttime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    amount = ''
                    phone = ''
                    status = 'Received'
                    txid = ''
                    
                    callback_type = msg.get('type', '')
                    
                    if callback_type == 'c2b_confirmation':
                        try:
                            txid = d.get('TransID', '')
                            amount = d.get('TransAmount', '')
                            phone = d.get('MSISDN', '')
                            
                            trans_time = d.get('TransTime', '')
                            if trans_time and len(trans_time) >= 14:
                                ttime = datetime.strptime(trans_time, '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
                            
                            name = d.get('FirstName', '')
                            ref = d.get('BillRefNumber', '')
                            status = f"✅ {d.get('TransactionType', '')} | Ref: {ref}"
                            if name:
                                status += f" | {name}"
                        except Exception:
                            pass
                            
                    elif 'stkCallback' in str(d):
                        try:
                            stk = d.get('Body', {}).get('stkCallback') if isinstance(d, dict) else None
                            if stk:
                                res_desc = stk.get('ResultDesc') or ''
                                res_code = stk.get('ResultCode')
                                status = f"{'✅' if res_code == 0 else '❌'} {res_desc}" if res_desc else (f"Code {res_code}" if res_code is not None else status)

                                txid = stk.get('MpesaReceiptNumber') or stk.get('CheckoutRequestID') or stk.get('MerchantRequestID') or ''

                                cb = stk.get('CallbackMetadata') or stk.get('Callback') or {}
                                items = cb.get('Item') if isinstance(cb, dict) else None
                                if not items and isinstance(cb, list):
                                    items = cb

                                if items and isinstance(items, list):
                                    for it in items:
                                        name = it.get('Name') or it.get('name')
                                        val = it.get('Value')
                                        if not name:
                                            continue
                                        if name.lower() == 'amount':
                                            amount = str(val)
                                        elif name.lower() in ('phonenumber', 'phone'):
                                            phone = str(val)
                                        elif name.lower() in ('mpesareceiptnumber',):
                                            txid = val or txid
                                        elif name.lower() in ('transactiondate',):
                                            try:
                                                s = str(val)
                                                if len(s) >= 14:
                                                    ttime = datetime.strptime(s[:14], '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
                                            except Exception:
                                                pass
                        except Exception:
                            pass

                    if amount and not amount.startswith('KES'):
                        amount = f"KES {amount}"

                    if phone and len(phone) > 4:
                        masked_digits = '*' * (len(phone) - 4)
                        phone = masked_digits + phone[-4:] 

                    # Update transactions
                    tx_page = self.pages.get('transactions')
                    if tx_page:
                        tx_page.add_transaction(ttime, amount, phone, status, txid)

                    # Show notification
                    def show_popup():
                        try:
                            title = 'Payment Notification'
                            lines = []

                            if callback_type == 'c2b_confirmation':
                                lines.extend([
                                    f"Transaction Type: {d.get('TransactionType', 'C2B')}",
                                    f"Amount: {amount}",
                                    f"Reference: {d.get('BillRefNumber', '')}",
                                    f"Phone: {phone}",
                                    f"Transaction ID: {txid}",
                                    f"Name: {d.get('FirstName', '')} {d.get('LastName', '')}"
                                ])
                            else:
                                lines.extend([
                                    f"Amount: {amount}",
                                    f"Phone: {phone}",
                                    f"Transaction ID: {txid}",
                                    f"Status: {status}"
                                ])

                            message = '\n'.join(filter(None, lines))

                            # System notification
                            try:
                                if plyer_notification:
                                    plyer_notification.notify(
                                        title=title,
                                        message=message,
                                        app_name='M-Pesa Manager',
                                        timeout=8
                                    )
                            except Exception:
                                pass

                            # Custom popup
                            try:
                                top = tk.Toplevel(self)
                                try:
                                    top.withdraw()
                                except Exception:
                                    pass

                                try:
                                    top.overrideredirect(True)
                                except Exception:
                                    pass

                                try:
                                    top.attributes('-topmost', True)
                                except Exception:
                                    pass

                                try:
                                    top.wm_attributes('-toolwindow', True)
                                except Exception:
                                    pass

                                frm = tk.Frame(top, bg=LIGHT, padx=12, pady=12, bd=1, relief='solid')
                                frm.pack(fill='both', expand=True)
                                lbl = tk.Label(frm, text=message, justify='left',
                                             bg=LIGHT, fg=TEXT_PRIMARY, wraplength=420)
                                lbl.pack(fill='both', expand=True)
                                btn = tk.Button(frm, text='Dismiss', command=top.destroy)
                                btn.pack(pady=(8, 0))

                                try:
                                    top.update_idletasks()
                                    w = top.winfo_reqwidth()
                                    h = top.winfo_reqheight()
                                    sw = top.winfo_screenwidth()
                                    sh = top.winfo_screenheight()
                                    x = (sw - w) // 2
                                    y = (sh - h) // 2
                                    top.geometry(f"{w}x{h}+{x}+{y}")
                                except Exception:
                                    pass

                                try:
                                    top.deiconify()
                                except Exception:
                                    pass
                                try:
                                    top.lift()
                                    top.focus_force()
                                except Exception:
                                    pass

                                if sys.platform.startswith('win'):
                                    try:
                                        hwnd = int(top.winfo_id())
                                        SWP_NOSIZE = 0x0001
                                        SWP_NOMOVE = 0x0002
                                        HWND_TOPMOST = -1
                                        ctypes.windll.user32.SetWindowPos(
                                            hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                                            SWP_NOMOVE | SWP_NOSIZE
                                        )
                                    except Exception:
                                        pass

                            except Exception:
                                try:
                                    messagebox.showinfo(title, message)
                                except Exception:
                                    pass

                        except Exception:
                            pass

                    self.after(0, show_popup)
                else:
                    self.after(0, lambda: messagebox.showinfo('Notification', str(msg)))
            except Exception as e:
                error_message = str(e)
                def show_error(message=error_message):
                    try:
                        messagebox.showerror('Notification Error', message)
                    except Exception:
                        pass
                self.after(0, show_error)

        # Connect to server
        connect_params = {}
        if token:
            connect_params['token'] = token
        if merchant_id:
            connect_params['merchant_id'] = merchant_id

        def run_client():
            try:
                qs = '&'.join([f"{k}={v}" for k, v in connect_params.items()])
                url = ws_url
                if qs:
                    url = f"{ws_url}?{qs}"
                    
                self._sio.connect(
                    url,
                    namespaces=['/'],
                    wait=True,
                    wait_timeout=10,
                    transports=('websocket',)
                )
                self._sio.wait()
            except Exception as e:
                error_message = str(e)
                def show_error(message=error_message):
                    try:
                        messagebox.showerror('Connection Error', message)
                    except Exception:
                        pass
                self.after(0, show_error)

        self._sio_thread = threading.Thread(target=run_client, daemon=True)
        self._sio_thread.start()

def main():
    app = MpesaManager()
    app.mainloop()

if __name__ == '__main__':
    main()