import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import QTimer
import requests

from ui.components.card_widgets import CardWidget
from ui.components.modern_buttons import ModernButton
from config import SERVER_URL


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