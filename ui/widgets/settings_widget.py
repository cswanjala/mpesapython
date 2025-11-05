import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFormLayout, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from pathlib import Path
import os

from ui.components.card_widgets import CardWidget
from ui.components.modern_inputs import ModernLineEdit, ModernComboBox
from ui.components.modern_buttons import ModernButton
import mpesa_client


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
                env_path = Path(__file__).parent.parent.parent.joinpath('.env').resolve()
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