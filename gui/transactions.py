import tkinter as tk
from tkinter import ttk
import requests
from .components import Card, FONT_FAMILY, FONT_SIZE, TEXT_PRIMARY, SURFACE, LIGHT

class Transactions(Card):
    """Transaction history view with real-time updates"""
    def __init__(self, parent):
        super().__init__(parent)
        self.add_title("Recent Transactions")
        
        # Create treeview for transactions
        columns = ("Time", "Amount", "Phone", "Status", "Transaction ID")
        self.tree = ttk.Treeview(self.content, columns=columns, show="headings")
        
        # Configure column headings
        for col in columns:
            self.tree.heading(col, text=col)
            # Adjust column widths
            if col == "Status":
                self.tree.column(col, width=200)
            elif col == "Transaction ID":
                self.tree.column(col, width=150)
            else:
                self.tree.column(col, width=100)
                
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.content, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.tree.pack(side="left", fill="both", expand=True, padx=(20,0), pady=20)
        scrollbar.pack(side="right", fill="y", padx=(0,20), pady=20)
        
    def add_transaction(self, time, amount, phone, status, txid):
        """Add a new transaction to the top of the list"""
        self.tree.insert("", 0, values=(time, amount, phone, status, txid))
        
    def load_from_server(self, server_url=None, limit=100):
        """Load transaction history from server"""
        if not server_url:
            return
            
        try:
            # Clear existing entries
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # Fetch transactions from server
            url = f"{server_url}/api/transactions"
            if limit:
                url += f"?limit={limit}"
                
            resp = requests.get(url)
            resp.raise_for_status()
            
            # Add transactions to tree
            for tx in resp.json():
                self.add_transaction(
                    tx.get('time', ''),
                    tx.get('amount', ''),
                    tx.get('phone', ''),
                    tx.get('status', ''),
                    tx.get('transaction_id', '')
                )
                
        except Exception as e:
            print(f"Error loading transactions: {e}")