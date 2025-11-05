import threading
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget
from PyQt6.QtCore import pyqtSignal

from ui.widgets.sidebar_widget import SidebarWidget
from ui.widgets.login_widget import LoginWidget
from ui.widgets.dashboard_widget import DashboardWidget
from ui.widgets.transactions_widget import TransactionsWidget
from ui.widgets.settings_widget import SettingsWidget
from ui.widgets.notification_widget import MultiDesktopNotificationWindow
from ui.network.ws_client import WSClient
from config import SERVER_URL


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('M-Pesa Manager - Professional Payment Gateway')
        self.resize(1200, 800)
        
        # Set window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8fafc;
            }
        """)
        
        # Central container with sidebar + stacked pages
        container = QWidget()
        h = QHBoxLayout()
        h.setSpacing(0)
        h.setContentsMargins(0, 0, 0, 0)
        container.setLayout(h)
        self.setCentralWidget(container)
        
        # Sidebar and pages
        self.sidebar = SidebarWidget()
        h.addWidget(self.sidebar)
        
        # Main content area
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("""
            QStackedWidget {
                background-color: #f8fafc;
                border: none;
            }
        """)
        h.addWidget(self.content_area, 1)
        
        # Initialize pages
        self.login = LoginWidget()
        self.dashboard = DashboardWidget()
        self.transactions = TransactionsWidget()
        self.settings = SettingsWidget()
        
        self.content_area.addWidget(self.login)
        self.content_area.addWidget(self.dashboard)
        self.content_area.addWidget(self.transactions)
        self.content_area.addWidget(self.settings)
        
        # Connect signals
        self.login.connected.connect(self.on_connected)
        
        # Wire sidebar buttons
        self.sidebar.nav_buttons['dashboard'].clicked.connect(lambda: self.switch_page('dashboard'))
        self.sidebar.nav_buttons['transactions'].clicked.connect(lambda: self.switch_page('transactions'))
        self.sidebar.nav_buttons['settings'].clicked.connect(lambda: self.switch_page('settings'))
        self.sidebar.nav_buttons['connect'].clicked.connect(lambda: self.switch_page('login'))
        
        # Store current state
        self._wsclient = None
        self._merchant_id = None
        self._shop_codes = None
        self._current_overlay = None
        
    def _on_notification(self, msg):
        """Handle incoming notifications by showing MULTI-DESKTOP overlay"""
        try:
            print(f"[GUI Debug] _on_notification received message: {msg}")
            formatted = self._format_notification(msg)
            
            # Add to dashboard history
            self.dashboard.append_history(f"🔔 {formatted}")
            
            # Add to transactions
            self.transactions.add_transaction(formatted)
            
            # Show MULTI-DESKTOP overlay that appears on ALL screens and virtual desktops
            self.show_multi_desktop_notification("💰 PAYMENT RECEIVED", formatted)
            
            print("[GUI Debug] Multi-desktop notification processed successfully")
            
        except Exception as e:
            print(f"[GUI Error] Error handling notification: {e}")
            import traceback
            print(traceback.format_exc())

    def switch_page(self, page_name):
        page_map = {
            'dashboard': self.dashboard,
            'transactions': self.transactions,
            'settings': self.settings,
            'login': self.login
        }
        if page_name in page_map:
            self.content_area.setCurrentWidget(page_map[page_name])
            
    def show_login(self):
        self.content_area.setCurrentWidget(self.login)

    def on_connected(self, payload):
        try:
            wsclient, shop_codes, merchant_id = payload
        except Exception:
            wsclient = payload
            shop_codes = None
            merchant_id = None

        self._wsclient = wsclient
        self._merchant_id = merchant_id
        self._shop_codes = shop_codes

        # Update sidebar status
        self.sidebar.set_connected(True)
        
        # Switch to dashboard
        self.content_area.setCurrentWidget(self.dashboard)
        self.dashboard.set_context(merchant_id, shop_codes)

        # Connect notifications
        try:
            print("[GUI Debug] Setting up notification handler...")
            wsclient.signals.notification.connect(self._on_notification)
            print("[GUI Debug] Notification handler connected successfully")
        except Exception as e:
            print(f"[GUI Error] Failed to connect notification handler: {e}")
            import traceback
            print(traceback.format_exc())

        # Pre-load transactions
        try:
            threading.Thread(target=self.transactions.load_from_server, args=(SERVER_URL, 200), daemon=True).start()
        except Exception:
            pass

    def show_multi_desktop_notification(self, title: str, message: str):
        """Show notification on ALL virtual desktops and ALL screens"""
        try:
            print(f"[MultiDesktop] Showing notification on ALL desktops - Title: {title}")

            # Create and show the MULTI-DESKTOP overlay
            overlay = MultiDesktopNotificationWindow(title, message)

            # Store reference to prevent garbage collection
            self._current_overlay = overlay

            # Show the overlay window (it will handle multiple screens/desktops)
            overlay.show()
            
            print(f"[MultiDesktop] Notification displayed on {len(overlay.notification_cards)} screens")
            
        except Exception as e:
            print(f"[MultiDesktop] Failed to show multi-desktop notification: {e}")
            import traceback
            print(traceback.format_exc())

    def _format_notification(self, msg):
        """Format notification message for display"""
        try:
            print(f"[GUI Debug] Formatting notification: {msg}")
            if isinstance(msg, dict):
                d = msg.get('data', {}) or {}
                t = msg.get('type', '')
                
                if t == 'c2b_confirmation' or isinstance(d, dict) and ('TransID' in d or 'TransAmount' in d):
                    txid = d.get('TransID') or d.get('TransID') or ''
                    amt = d.get('TransAmount') or d.get('Amount') or ''
                    phone = d.get('MSISDN') or d.get('Phone') or ''
                    name = (d.get('FirstName') or '') + ' ' + (d.get('LastName') or '')
                    formatted = f"NEW PAYMENT CONFIRMED!\n\n💵 Amount: KES {amt}\n📱 From: {phone}\n👤 Customer: {name.strip()}\n🔢 Reference: {txid}"
                    print(f"[GUI Debug] Formatted notification: {formatted}")
                    return formatted

                if 'stkCallback' in str(d) or 'stkCallback' in str(msg):
                    stk = None
                    if isinstance(d, dict):
                        stk = d.get('Body', {}).get('stkCallback') or d.get('stkCallback')
                    if not stk and isinstance(msg, dict):
                        stk = msg.get('stkCallback')
                    if stk and isinstance(stk, dict):
                        res_desc = stk.get('ResultDesc') or ''
                        res_code = stk.get('ResultCode')
                        cb = stk.get('CallbackMetadata') or stk.get('Callback') or {}
                        items = cb.get('Item') if isinstance(cb, dict) else (cb if isinstance(cb, list) else None)
                        amt = ''
                        phone = ''
                        txid = stk.get('MpesaReceiptNumber') or stk.get('CheckoutRequestID') or ''
                        if items and isinstance(items, list):
                            for it in items:
                                name = it.get('Name') or it.get('name')
                                val = it.get('Value')
                                if not name:
                                    continue
                                if name.lower() == 'amount':
                                    amt = str(val)
                                if name.lower() in ('phonenumber', 'phone'):
                                    phone = str(val)
                        
                        if res_code == 0:
                            return f"✅ PAYMENT SUCCESSFUL!\n\n💵 Amount: KES {amt}\n📱 Phone: {phone}\n🧾 Receipt: {txid}"
                        else:
                            return f"❌ PAYMENT FAILED\n\n📱 Phone: {phone}\n⚠️ Reason: {res_desc}"

            # Fallback for unknown format
            return f"NEW TRANSACTION\n\n{str(msg)}"
            
        except Exception:
            return f"NEW TRANSACTION\n\n{str(msg)}"