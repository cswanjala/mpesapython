from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QMessageBox
from PyQt6.QtCore import pyqtSignal, Qt
import threading

from ui.components.card_widgets import CardWidget
from ui.components.modern_inputs import ModernLineEdit, ModernComboBox
from ui.components.modern_buttons import ModernButton
from ui.network.ws_client import WSClient
from config import SERVER_URL, WEBSOCKET_URL, SHOP_MAP


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