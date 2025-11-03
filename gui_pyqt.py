import sys
import threading
import socketio
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox, QTextEdit, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout, QFrame,
    QGroupBox, QScrollArea, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap, QGuiApplication, QScreen

import mpesa_client
from config import SERVER_URL, WEBSOCKET_URL, SHOP_MAP
import ctypes
import platform

# Optional Windows native toast notifier (for sound and system toast)
try:
    from winotify import Notification, audio
    _HAS_WINOTIFY = True
except Exception:
    _HAS_WINOTIFY = False


class MultiDesktopNotificationWindow(QWidget):
    """A notification that appears on ALL virtual desktops and ALL screens"""
    
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        
        # ULTRA-FORCEFUL window flags for multi-desktop support
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |          # Always on top
            Qt.WindowType.FramelessWindowHint |           # No title bar
            Qt.WindowType.Tool |                          # No taskbar entry
            Qt.WindowType.X11BypassWindowManagerHint |    # Bypass window manager (Linux)
            Qt.WindowType.WindowDoesNotAcceptFocus |      # Don't steal focus
            Qt.WindowType.MSWindowsFixedSizeDialogHint    # Better multi-desktop support on Windows
        )
        
        # Make it truly top-most and visible on all virtual desktops
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Create notification cards for ALL screens
        self.notification_cards = []
        self.create_notifications_for_all_screens(title, message)
        
        # Auto-close timer
        self.auto_close_timer = QTimer()
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(self.animate_out)
        self.auto_close_timer.start(15000)  # 15 seconds
        
        # Force to top immediately on all desktops
        QTimer.singleShot(100, self.force_to_all_desktops)
        
    def create_notifications_for_all_screens(self, title: str, message: str):
        """Create notification cards for EVERY screen and virtual desktop"""
        screens = QGuiApplication.screens()
        print(f"[MultiDesktop] Creating notifications for {len(screens)} screens")
        
        for screen in screens:
            # Create a notification card for each screen
            card = PaymentNotificationCard(title, message, self)
            card.dismissed.connect(self.on_card_dismissed)
            self.notification_cards.append(card)
            
            # Position card at center of this specific screen
            self.center_notification_on_screen(card, screen)
            
    def center_notification_on_screen(self, card, screen):
        """Position the notification card at bottom-right of the given screen (like a toast)"""
        geo = screen.geometry()
        margin = 32
        x = geo.x() + geo.width() - card.width() - margin
        y = geo.y() + geo.height() - card.height() - margin

        card.move(x, y)
        card.show()
        
    def showEvent(self, event):
        """Animate in when shown"""
        super().showEvent(event)
        self.force_to_all_desktops()
        for card in self.notification_cards:
            card.animate_in()
        
    def force_to_all_desktops(self):
        """Force the window to be visible on ALL virtual desktops using platform-specific methods"""
        try:
            if platform.system() == 'Windows':
                self._force_windows_all_desktops()
            elif platform.system() == 'Linux':
                self._force_linux_all_desktops()
            else:  # macOS and others
                self._force_generic_all_desktops()
                
            # Force all cards to be visible
            for card in self.notification_cards:
                card.raise_()
                card.activateWindow()
                card.show()
                
        except Exception as e:
            print(f"[MultiDesktop] Error forcing to all desktops: {e}")
            
    def _force_windows_all_desktops(self):
        """Windows-specific: Make window visible on all virtual desktops"""
        try:
            # Try to use Windows API to show on all virtual desktops
            HWND_TOPMOST = -1
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_SHOWWINDOW = 0x0040
            flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
            
            for card in self.notification_cards:
                hwnd = int(card.winId())
                # Set as topmost
                ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags)
                # Additional forceful methods
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                
                # Try to make it visible on all virtual desktops (Windows 10+)
                try:
                    # This is the key for virtual desktop support
                    GWL_EXSTYLE = -20
                    WS_EX_TOOLWINDOW = 0x00000080
                    WS_EX_NOACTIVATE = 0x08000000
                    
                    # Get current style
                    current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                    # Add toolwindow and noactivate flags for better multi-desktop behavior
                    new_style = current_style | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
                    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
                    
                except Exception as e:
                    print(f"[Windows Virtual Desktop] Fallback: {e}")
                    
        except Exception as e:
            print(f"[Windows All Desktops Error] {e}")
            
    def _force_linux_all_desktops(self):
        """Linux-specific: Make window visible on all workspaces"""
        try:
            for card in self.notification_cards:
                hwnd = int(card.winId())
                # Use xdotool to set on all workspaces
                import subprocess
                wid = hex(hwnd)
                # Try to set sticky flag (visible on all workspaces)
                subprocess.run(['xdotool', 'set_window', '--classname', 'MPesaNotification', wid], timeout=2)
                subprocess.run(['wmctrl', '-i', '-r', wid, '-b', 'add,sticky'], timeout=2)
        except:
            # Fallback - just ensure visibility
            for card in self.notification_cards:
                card.raise_()
                card.show()
            
    def _force_generic_all_desktops(self):
        """Generic method for other platforms"""
        for card in self.notification_cards:
            card.raise_()
            card.activateWindow()
            card.show()
            
    def on_card_dismissed(self):
        """When any card is dismissed, dismiss all"""
        self.animate_out()
        
    def animate_out(self):
        """Animate out and close all cards"""
        for card in self.notification_cards:
            card.animate_out()
        QTimer.singleShot(500, self.close_all)
        
    def close_all(self):
        """Close all notification cards"""
        for card in self.notification_cards:
            card.close()
        self.close()


class PaymentNotificationCard(QWidget):
    """A toast-style payment notification card (small, bottom-right, rounded, shadowed)"""
    dismissed = pyqtSignal()

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setFixedSize(340, 110)
        self.setStyleSheet("""
            QWidget {
                background: rgba(30, 41, 59, 0.96);
                border-radius: 16px;
                border: 1.5px solid #2563eb;
                color: #f1f5f9;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)
        
        # Header: icon and title
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("💰")
        icon_label.setStyleSheet("font-size: 22px; margin-right: 8px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #f1f5f9; margin: 0px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(22, 22)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #f1f5f9;
                border: none;
                border-radius: 11px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: white;
            }
        """)
        close_btn.clicked.connect(self.on_dismiss)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Message content
        message_label = QLabel(message)
        message_label.setStyleSheet("font-size: 13px; color: #e0e7ef; line-height: 1.5; margin-top: 2px;")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Timestamp
        timestamp = QLabel(datetime.now().strftime("%H:%M:%S"))
        timestamp.setStyleSheet("font-size: 11px; color: #a5b4fc; font-style: italic; margin-top: 2px;")
        layout.addWidget(timestamp)
        
        self.setLayout(layout)
        
        # Fade in effect
        self.setWindowOpacity(0.0)
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(350)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(31, 38, 135, 90))
        self.setGraphicsEffect(shadow)
        
        # Play sound if available
        self._play_notification_sound()
        
    def _play_notification_sound(self):
        """Play a notification sound on ALL platforms"""
        try:
            if platform.system() == 'Windows':
                import winsound
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
            elif platform.system() == 'Darwin':  # macOS
                import os
                os.system('afplay /System/Library/Sounds/Glass.aiff &')
            elif platform.system() == 'Linux':
                import os
                os.system('paplay /usr/share/sounds/freedesktop/stereo/message.oga &')
        except Exception as e:
            print(f"[Toast] Sound error: {e}")
            
    def setup_animation(self):
        pass  # No longer needed for toast style
    
    def animate_in(self):
        # Fade in (already handled in __init__)
        pass
    
    def animate_out(self):
        """Fade out and close"""
        fade = QPropertyAnimation(self, b"windowOpacity")
        fade.setDuration(300)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.finished.connect(self.close)
        fade.start()
        
    def on_dismiss(self):
        self.animate_out()
        QTimer.singleShot(400, self.dismissed.emit)


class ModernButton(QPushButton):
    def __init__(self, text, primary=False, size="medium"):
        super().__init__(text)
        
        sizes = {
            "small": "padding: 6px 12px; font-size: 12px;",
            "medium": "padding: 8px 16px; font-size: 14px;",
            "large": "padding: 12px 24px; font-size: 16px;"
        }
        
        base_style = """
            QPushButton {
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                margin-top: -1px;
            }
            QPushButton:pressed {
                margin-top: 1px;
            }
        """
        
        if primary:
            self.setStyleSheet(base_style + sizes[size] + """
                QPushButton {
                    background-color: #2563eb;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #1d4ed8;
                }
                QPushButton:disabled {
                    background-color: #93c5fd;
                    color: #dbeafe;
                }
            """)
        else:
            self.setStyleSheet(base_style + sizes[size] + """
                QPushButton {
                    background-color: #f8fafc;
                    color: #334155;
                    border: 1px solid #e2e8f0;
                }
                QPushButton:hover {
                    background-color: #f1f5f9;
                    border-color: #cbd5e1;
                }
                QPushButton:disabled {
                    background-color: #f8fafc;
                    color: #94a3b8;
                }
            """)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class ModernLineEdit(QLineEdit):
    def __init__(self, placeholder="", password=False):
        super().__init__()
        self.setPlaceholderText(placeholder)
        
        if password:
            self.setEchoMode(QLineEdit.EchoMode.Password)
            
        self.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
                selection-background-color: #dbeafe;
            }
            QLineEdit:focus {
                border-color: #2563eb;
                outline: none;
            }
            QLineEdit:hover {
                border-color: #cbd5e1;
            }
        """)


class ModernComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #cbd5e1;
            }
            QComboBox:focus {
                border-color: #2563eb;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #64748b;
                width: 0px;
                height: 0px;
            }
        """)


class CardWidget(QFrame):
    def __init__(self, title="", content_widget=None):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            CardWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                font-size: 18px;
                font-weight: 700;
                color: #1e293b;
                margin: 0px;
            """)
            layout.addWidget(title_label)
        
        if content_widget:
            layout.addWidget(content_widget)
        
        self.setLayout(layout)


class SidebarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self.setStyleSheet("""
            SidebarWidget {
                background-color: #1e293b;
                color: white;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(8)
        
        # Logo/Header
        header = QLabel("M-Pesa Manager")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #f8fafc;
            padding: 20px;
            border-bottom: 1px solid #334155;
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Navigation buttons
        self.nav_buttons = {}
        
        nav_items = [
            ("Dashboard", "📊"),
            ("Transactions", "💳"),
            ("Settings", "⚙️"),
            ("Connect", "🔗")
        ]
        
        for text, icon in nav_items:
            btn = QPushButton(f"{icon}  {text}")
            btn.setFixedHeight(44)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #cbd5e1;
                    border: none;
                    text-align: left;
                    padding: 0px 20px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #334155;
                    color: #f8fafc;
                }
                QPushButton:pressed {
                    background-color: #475569;
                }
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(btn)
            self.nav_buttons[text.lower()] = btn
        
        layout.addStretch()
        
        # Status indicator
        status_widget = QWidget()
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(20, 10, 20, 10)
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #ef4444; font-size: 16px;")
        status_label = QLabel("Disconnected")
        status_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        status_widget.setLayout(status_layout)
        
        layout.addWidget(status_widget)
        self.setLayout(layout)
    
    def set_connected(self, connected):
        if connected:
            self.status_indicator.setStyleSheet("color: #10b981; font-size: 16px;")
        else:
            self.status_indicator.setStyleSheet("color: #ef4444; font-size: 16px;")


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


class LoginWidget(QWidget):
    connected = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.wsclient = None

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(100, 50, 100, 50)
        layout.setSpacing(30)
        self.setLayout(layout)
        
        # Header
        header = QLabel("Connect to M-Pesa Manager")
        header.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 10px;
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        subheader = QLabel("Enter your credentials to connect to the payment gateway")
        subheader.setStyleSheet("""
            font-size: 16px;
            color: #64748b;
            margin-bottom: 40px;
        """)
        subheader.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subheader)
        
        # Login Card
        login_card = CardWidget()
        login_layout = login_card.layout()
        
        form = QFormLayout()
        form.setVerticalSpacing(15)
        form.setHorizontalSpacing(20)
        
        # Server URL
        server_label = QLabel("Server URL")
        server_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.server_edit = ModernLineEdit("http://localhost:5000")
        self.server_edit.setText(SERVER_URL or 'http://localhost:5000')
        form.addRow(server_label, self.server_edit)
        
        # Shop Selection
        shop_label = QLabel("Shop")
        shop_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.shop_combo = ModernComboBox()
        for k in SHOP_MAP.keys():
            self.shop_combo.addItem(k)
        form.addRow(shop_label, self.shop_combo)
        
        # Username
        user_label = QLabel("Merchant ID")
        user_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.user_edit = ModernLineEdit("Enter your merchant ID")
        form.addRow(user_label, self.user_edit)
        
        # Password
        pass_label = QLabel("Password")
        pass_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.user_pass = ModernLineEdit("", password=True)
        form.addRow(pass_label, self.user_pass)
        
        login_layout.addLayout(form)
        
        # Connect Button
        self.connect_btn = ModernButton("Connect to Server", primary=True, size="large")
        self.connect_btn.setFixedHeight(44)
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        login_layout.addWidget(self.connect_btn)
        
        # Status
        self.status_label = QLabel("Ready to connect")
        self.status_label.setStyleSheet("color: #64748b; font-size: 14px; text-align: center;")
        login_layout.addWidget(self.status_label)
        
        layout.addWidget(login_card)
        layout.addStretch()

    def on_connect_clicked(self):
        server = self.server_edit.text().rstrip('/')
        username = self.user_edit.text().strip()
        shop_name = self.shop_combo.currentText()

        if not username:
            QMessageBox.critical(self, 'Error', 'Please enter Merchant ID')
            return

        shop_codes = SHOP_MAP.get(shop_name)
        if isinstance(shop_codes, (list, tuple)):
            shop_codes = [str(s) for s in shop_codes]
        elif shop_codes is not None:
            shop_codes = [str(shop_codes)]

        ws_url = WEBSOCKET_URL or server

        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("Connecting...")
        self.status_label.setText("Establishing connection...")
        self.status_label.setStyleSheet("color: #f59e0b; font-size: 14px;")

        self._shop_codes = shop_codes
        self._merchant_id = username
        self.wsclient = WSClient(ws_url, token=None, merchant_id=username, shop_codes=shop_codes)
        self.wsclient.signals.connected.connect(self._on_connected)
        self.wsclient.signals.disconnected.connect(self._on_disconnected)
        self.wsclient.signals.error.connect(self._on_error)
        self.wsclient.signals.notification.connect(self._on_notification)
        self.wsclient.start()

    def _on_connected(self):
        self.status_label.setText('Connected successfully')
        self.status_label.setStyleSheet("color: #10b981; font-size: 14px;")
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Connect to Server")
        try:
            self.connected.emit((self.wsclient, self._shop_codes, self._merchant_id))
        except Exception:
            self.connected.emit((self.wsclient, None, self._merchant_id))

    def _on_disconnected(self):
        self.status_label.setText('Disconnected')
        self.status_label.setStyleSheet("color: #ef4444; font-size: 14px;")

    def _on_error(self, msg):
        self.status_label.setText('Connection failed')
        self.status_label.setStyleSheet("color: #ef4444; font-size: 14px;")
        QMessageBox.critical(self, 'Connection Error', str(msg))
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Connect to Server")

    def _on_notification(self, payload):
        # This will now use the global overlay
        pass


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._merchant_id = None
        self._shop_codes = None
        self._build_ui()

    def set_context(self, merchant_id, shop_codes):
        self._merchant_id = merchant_id
        self._shop_codes = shop_codes

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        self.setLayout(layout)
        
        # Header
        header = QLabel("Payment Dashboard")
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 10px;
        """)
        layout.addWidget(header)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left column - STK Push form
        left_column = QVBoxLayout()
        left_column.setSpacing(20)
        
        # STK Push Card
        stk_card = CardWidget("Send STK Push")
        stk_layout = stk_card.layout()
        
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(15)
        
        # Phone input
        phone_label = QLabel("Phone Number")
        phone_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.phone_edit = ModernLineEdit("2547XXXXXXXX")
        form_layout.addRow(phone_label, self.phone_edit)
        
        # Amount input
        amount_label = QLabel("Amount (KES)")
        amount_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.amount_edit = ModernLineEdit("100")
        form_layout.addRow(amount_label, self.amount_edit)
        
        stk_layout.addLayout(form_layout)
        
        # Send button
        self.send_btn = ModernButton("Send STK Push", primary=True, size="large")
        self.send_btn.setFixedHeight(44)
        self.send_btn.clicked.connect(self.on_send)
        stk_layout.addWidget(self.send_btn)
        
        left_column.addWidget(stk_card)
        left_column.addStretch()
        
        # Right column - Activity feed
        right_column = QVBoxLayout()
        right_column.setSpacing(20)
        
        # Activity card
        activity_card = CardWidget("Recent Activity")
        activity_layout = activity_card.layout()
        
        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.history.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 12px;
                font-family: 'Monospace';
                font-size: 12px;
                background-color: #f8fafc;
            }
        """)
        self.history.setMinimumHeight(300)
        activity_layout.addWidget(self.history)
        
        right_column.addWidget(activity_card)
        right_column.addStretch()
        
        content_layout.addLayout(left_column, 1)
        content_layout.addLayout(right_column, 1)
        layout.addLayout(content_layout)

    def on_send(self):
        phone = self.phone_edit.text().strip()
        amount = self.amount_edit.text().strip()
        
        if not phone or not amount:
            QMessageBox.critical(self, 'Error', 'Please enter both phone number and amount')
            return
            
        try:
            amt = int(float(amount))
        except ValueError:
            QMessageBox.critical(self, 'Error', 'Please enter a valid amount')
            return

        self.append_history(f'🚀 Sending STK Push to {phone} for KES {amt:,}...')
        self.send_btn.setEnabled(False)
        self.send_btn.setText("Sending...")
        
        threading.Thread(target=self._send_stk_bg, args=(phone, amt), daemon=True).start()

    def _send_stk_bg(self, phone, amount):
        try:
            shortcode_to_use = None
            try:
                if isinstance(self._shop_codes, (list, tuple)) and len(self._shop_codes) > 0:
                    shortcode_to_use = str(self._shop_codes[0])
                elif self._shop_codes is not None:
                    shortcode_to_use = str(self._shop_codes)
            except Exception:
                shortcode_to_use = None

            if shortcode_to_use:
                resp = mpesa_client.lipa_na_mpesa_online(phone, int(amount), merchant_id=self._merchant_id, shortcode=shortcode_to_use)
            else:
                resp = mpesa_client.lipa_na_mpesa_online(phone, int(amount), merchant_id=self._merchant_id)
                
            text = getattr(resp, 'text', str(resp))
            self.append_history(f'✅ STK Push sent successfully\n   Response: {text}')
            QMessageBox.information(self, 'Success', f'STK Push initiated successfully!\nResponse: {text}')
            
        except Exception as e:
            self.append_history(f'❌ STK Push failed: {str(e)}')
            QMessageBox.critical(self, 'Error', f'Failed to send STK Push:\n{str(e)}')
        finally:
            self.send_btn.setEnabled(True)
            self.send_btn.setText("Send STK Push")

    def append_history(self, msg):
        ts = datetime.now().strftime('%H:%M:%S')
        self.history.append(f'[{ts}] {msg}')


class TransactionsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        self.setLayout(layout)
        
        # Header with refresh button
        header_layout = QHBoxLayout()
        
        title = QLabel("Transaction History")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #1e293b;
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.refresh_btn = ModernButton("Refresh", size="small")
        self.refresh_btn.clicked.connect(self.on_refresh)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Transactions table card
        table_card = CardWidget()
        table_layout = table_card.layout()
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(['Time', 'Amount', 'Phone', 'Status', 'Transaction ID'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Style the table
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #e2e8f0;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f5f9;
            }
            QTableWidget::item:selected {
                background-color: #dbeafe;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                font-weight: 600;
                color: #374151;
            }
        """)
        
        table_layout.addWidget(self.table)
        layout.addWidget(table_card)

    def on_refresh(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Refreshing...")
        
        def refresh_complete():
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("Refresh")
            
        threading.Thread(target=self._refresh_data, daemon=True).start()
        QTimer.singleShot(2000, refresh_complete)

    def _refresh_data(self):
        self.load_from_server()

    def add_transaction(self, time_or_text, amount=None, phone=None, status=None, txid=None):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        if amount is None and isinstance(time_or_text, str) and '|' in time_or_text:
            parts = [p.strip() for p in time_or_text.split('|')]
            vals = parts + [''] * (5 - len(parts))
        elif amount is None and isinstance(time_or_text, str):
            vals = [time_or_text, '', '', '', '']
        else:
            vals = [
                str(time_or_text or ''),
                str(amount or ''),
                str(phone or ''),
                str(status or ''),
                str(txid or '')
            ]

        for c in range(5):
            item = QTableWidgetItem(vals[c])
            self.table.setItem(row, c, item)

    def load_from_server(self, server_url=None, limit=100):
        import requests
        if not server_url:
            server_url = SERVER_URL or "http://localhost:5000"  # Default to localhost if not configured
            
        print(f"[GUI Debug] Using server URL: {server_url}")
            
        if not server_url:
            print("[GUI Debug] No server URL configured for transactions")
            self.add_transaction("No server URL configured")
            return
            
        try:
            url = f"{server_url}/api/transactions"
            if limit:
                url += f"?limit={limit}"
            print(f"[GUI Debug] Loading transactions from: {url}")
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            
            data = resp.json()
            print(f"[GUI Debug] Received {len(data)} transactions from server")
            
            self.table.setRowCount(0)
            
            for tx in data:
                self.add_transaction(
                    tx.get('time', ''),
                    tx.get('amount', ''),
                    tx.get('phone', ''),
                    tx.get('status', ''),
                    tx.get('transaction_id', '')
                )
            print("[GUI Debug] Transaction table updated successfully")
                
        except Exception as e:
            print(f"[GUI Error] Failed to load transactions: {e}")
            import traceback
            print(traceback.format_exc())
            self.add_transaction(f'Failed to load transactions: {e}')


class SettingsWidget(QWidget):
    register_done = pyqtSignal(object)
    save_done = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        self.setLayout(layout)
        
        # Header
        header = QLabel("Settings & Configuration")
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 10px;
        """)
        layout.addWidget(header)
        
        # Settings cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Left column - Credentials
        left_column = QVBoxLayout()
        left_column.setSpacing(20)
        
        # Credentials card
        cred_card = CardWidget("M-Pesa Credentials")
        cred_layout = cred_card.layout()
        
        form = QFormLayout()
        form.setVerticalSpacing(12)
        form.setHorizontalSpacing(15)
        
        # Consumer Key
        consumer_label = QLabel("Consumer Key")
        consumer_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.consumer_entry = ModernLineEdit()
        self.consumer_entry.setText(str(getattr(__import__('config'), 'CONSUMER_KEY', '') or ''))
        form.addRow(consumer_label, self.consumer_entry)
        
        # Consumer Secret
        secret_label = QLabel("Consumer Secret")
        secret_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.consumer_secret_entry = ModernLineEdit()
        self.consumer_secret_entry.setText(str(getattr(__import__('config'), 'CONSUMER_SECRET', '') or ''))
        form.addRow(secret_label, self.consumer_secret_entry)
        
        # Passkey
        passkey_label = QLabel("Passkey")
        passkey_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.passkey_entry = ModernLineEdit()
        self.passkey_entry.setText(str(getattr(__import__('config'), 'PASSKEY', '') or ''))
        form.addRow(passkey_label, self.passkey_entry)
        
        # Shortcode
        shortcode_label = QLabel("Shortcode")
        shortcode_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.shortcode_entry = ModernLineEdit()
        self.shortcode_entry.setText(str(getattr(__import__('config'), 'SHORTCODE', '') or ''))
        form.addRow(shortcode_label, self.shortcode_entry)
        
        cred_layout.addLayout(form)
        
        # Save button
        self.save_btn = ModernButton("Save Credentials", primary=True)
        self.save_btn.clicked.connect(self.save_credentials)
        cred_layout.addWidget(self.save_btn)
        
        left_column.addWidget(cred_card)
        
        # Right column - URLs
        right_column = QVBoxLayout()
        right_column.setSpacing(20)
        
        # URLs card
        urls_card = CardWidget("URL Configuration")
        urls_layout = urls_card.layout()
        
        urls_form = QFormLayout()
        urls_form.setVerticalSpacing(12)
        urls_form.setHorizontalSpacing(15)
        
        # Callback URL
        callback_label = QLabel("STK Callback URL")
        callback_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.stk_callback_entry = ModernLineEdit()
        self.stk_callback_entry.setText(str(getattr(__import__('config'), 'CALLBACK_URL', '') or ''))
        urls_form.addRow(callback_label, self.stk_callback_entry)
        
        # Validation URL
        validation_label = QLabel("Validation URL")
        validation_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.validation_entry = ModernLineEdit()
        urls_form.addRow(validation_label, self.validation_entry)
        
        # Confirmation URL
        confirmation_label = QLabel("Confirmation URL")
        confirmation_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.confirmation_entry = ModernLineEdit()
        urls_form.addRow(confirmation_label, self.confirmation_entry)
        
        # Response Type
        response_label = QLabel("Response Type")
        response_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.response_type = ModernComboBox()
        self.response_type.addItems(['Completed', 'Cancelled'])
        urls_form.addRow(response_label, self.response_type)
        
        urls_layout.addLayout(urls_form)
        
        # Register button
        self.register_btn = ModernButton("Register URLs", primary=True)
        self.register_btn.clicked.connect(self.register_urls)
        urls_layout.addWidget(self.register_btn)
        
        right_column.addWidget(urls_card)
        
        cards_layout.addLayout(left_column)
        cards_layout.addLayout(right_column)
        layout.addLayout(cards_layout)
        
        # Note
        note = QLabel("Credentials are stored in .env file at project root")
        note.setStyleSheet("color: #64748b; font-size: 14px; font-style: italic;")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(note)

    def register_urls(self):
        shortcode = self.shortcode_entry.text().strip()
        validation_url = self.validation_entry.text().strip()
        confirmation_url = self.confirmation_entry.text().strip()
        response_type = self.response_type.currentText()
        
        if not all([shortcode, validation_url, confirmation_url]):
            QMessageBox.critical(self, 'Error', 'Please fill all required fields: shortcode, validation and confirmation URLs')
            return
            
        self.register_btn.setEnabled(False)
        self.register_btn.setText("Registering...")

        def worker():
            try:
                res = mpesa_client.register_c2b_urls(
                    shortcode=shortcode, 
                    confirmation_url=confirmation_url, 
                    validation_url=validation_url, 
                    response_type=response_type
                )
                self.register_done.emit(res)
            except Exception as e:
                self.register_done.emit(e)

        threading.Thread(target=worker, daemon=True).start()
        self.register_done.connect(self._on_register_done)

    def save_credentials(self):
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Saving...")

        def worker():
            try:
                import os
                from pathlib import Path
                env_path = Path(__file__).parent.joinpath('..', '.env').resolve()
                env_vars = {}
                if env_path.exists():
                    with open(env_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if '=' in line and not line.strip().startswith('#'):
                                k, v = line.strip().split('=', 1)
                                env_vars[k] = v

                updates = {
                    'CONSUMER_KEY': self.consumer_entry.text().strip(),
                    'CONSUMER_SECRET': self.consumer_secret_entry.text().strip(),
                    'PASSKEY': self.passkey_entry.text().strip(),
                    'CALLBACK_URL': self.stk_callback_entry.text().strip(),
                    'SHORTCODE': self.shortcode_entry.text().strip()
                }
                env_vars.update(updates)
                
                with open(env_path, 'w', encoding='utf-8') as f:
                    for k, v in env_vars.items():
                        f.write(f"{k}={v}\n")
                self.save_done.emit(True)
            except Exception as e:
                self.save_done.emit(e)

        threading.Thread(target=worker, daemon=True).start()
        self.save_done.connect(self._on_save_done)

    def _on_register_done(self, result):
        self.register_btn.setEnabled(True)
        self.register_btn.setText("Register URLs")
        if isinstance(result, Exception):
            QMessageBox.critical(self, 'Error', f'Failed to register URLs:\n{str(result)}')
        else:
            QMessageBox.information(self, 'Success', 'URLs registered successfully!')

    def _on_save_done(self, result):
        self.save_btn.setEnabled(True)
        self.save_btn.setText("Save Credentials")
        if isinstance(result, Exception):
            QMessageBox.critical(self, 'Error', f'Failed to save credentials:\n{str(result)}')
        else:
            QMessageBox.information(self, 'Success', 'Credentials saved successfully!')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        print("[GUI Debug] Initializing MainWindow with Multi-Desktop Support")
        self.setWindowTitle('M-Pesa Manager - Professional Payment Gateway')
        self.resize(1200, 800)
        
        # Set window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8fafc;
            }
        """)
        
        print("[GUI Debug] Creating central container")
        # Central container with sidebar + stacked pages
        container = QWidget()
        h = QHBoxLayout()
        h.setSpacing(0)
        h.setContentsMargins(0, 0, 0, 0)
        container.setLayout(h)
        self.setCentralWidget(container)
        
        print("[GUI Debug] Setting up sidebar")
        # Sidebar and pages
        self.sidebar = SidebarWidget()
        h.addWidget(self.sidebar)
        
        print("[GUI Debug] Creating content area")
        # Main content area
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("""
            QStackedWidget {
                background-color: #f8fafc;
                border: none;
            }
        """)
        h.addWidget(self.content_area, 1)
        
        print("[GUI Debug] Initializing pages")
        # Initialize pages
        self.login = LoginWidget()
        self.dashboard = DashboardWidget()
        self.transactions = TransactionsWidget()
        self.settings = SettingsWidget()
        
        print("[GUI Debug] Adding pages to stacked widget")
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
        
        print("[GUI Debug] MainWindow initialization complete")
        
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

            # Show Windows toast for sound (this appears in Action Center across desktops)
            if platform.system() == 'Windows' and _HAS_WINOTIFY:
                try:
                    toast = Notification(
                        app_id="M-Pesa Manager",
                        title="💰 PAYMENT RECEIVED",
                        msg=message.split('\n')[0] if '\n' in message else message,
                        duration="long"
                    )
                    toast.set_audio(audio.Default, loop=False)
                    toast.show()
                    print("[MultiDesktop] Windows toast notification shown")
                except Exception as e:
                    print(f"[MultiDesktop] Failed to show Windows toast: {e}")

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


def main():
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    print("[GUI Debug] Starting application with Multi-Desktop Support...")
    mw = MainWindow()
    print("[GUI Debug] Main window created")
    
    # Default to login widget on startup
    mw.content_area.setCurrentWidget(mw.login)
    print("[GUI Debug] Set initial widget to login")
    
    # Show the window
    mw.show()
    print("[GUI Debug] Main window displayed")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()