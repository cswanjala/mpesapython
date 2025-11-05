import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFormLayout, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
import mpesa_client

from ui.components.card_widgets import CardWidget
from ui.components.modern_inputs import ModernLineEdit
from ui.components.modern_buttons import ModernButton


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
        from datetime import datetime
        ts = datetime.now().strftime('%H:%M:%S')
        self.history.append(f'[{ts}] {msg}')