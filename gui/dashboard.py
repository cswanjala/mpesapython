import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import os
from .components import Card, ModernButton, FONT_FAMILY, FONT_SIZE, TEXT_PRIMARY, SURFACE, LIGHT

class Dashboard(Card):
    """Main dashboard with STK push functionality and history"""
    def __init__(self, parent, stk_callback):
        super().__init__(parent)
        self.stk_callback = stk_callback
        
        self.add_title("Send STK Push")
        
        # STK Push form
        form = tk.Frame(self.content, bg=SURFACE)
        form.pack(fill="x", padx=20, pady=10)
        
        # Phone number input
        phone_row = tk.Frame(form, bg=SURFACE)
        phone_row.pack(fill="x", pady=8)
        tk.Label(phone_row, text="Phone Number:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                fg=TEXT_PRIMARY, bg=SURFACE, width=15, anchor="w").pack(side="left")
        self.phone_entry = tk.Entry(phone_row, font=(FONT_FAMILY, FONT_SIZE+1),
                                  relief="solid", bd=1, bg=LIGHT)
        self.phone_entry.pack(side="left", fill="x", expand=True, ipady=4)
        
        # Amount input
        amount_row = tk.Frame(form, bg=SURFACE)
        amount_row.pack(fill="x", pady=8)
        tk.Label(amount_row, text="Amount (KES):", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                fg=TEXT_PRIMARY, bg=SURFACE, width=15, anchor="w").pack(side="left")
        self.amount_entry = tk.Entry(amount_row, font=(FONT_FAMILY, FONT_SIZE+1),
                                   relief="solid", bd=1, bg=LIGHT)
        self.amount_entry.pack(side="left", fill="x", expand=True, ipady=4)
        
        # Send button
        btn_row = tk.Frame(form, bg=SURFACE)
        btn_row.pack(fill="x", pady=(20, 0))
        self.send_btn = ModernButton(btn_row, "Send STK Push", self.send_stk, "primary")
        self.send_btn.pack()
        
        # History section
        self.add_title("History", pady=(30, 10))
        self.history = tk.Text(self.content, font=(FONT_FAMILY, FONT_SIZE),
                             bg=LIGHT, relief="solid", bd=1, height=10)
        self.history.pack(fill="both", expand=True, padx=20, pady=10)
        
    def send_stk(self):
        """Validate and send STK push request"""
        phone = self.phone_entry.get().strip()
        amount = self.amount_entry.get().strip()
        
        # Basic validation
        if not phone or not amount:
            messagebox.showerror("Error", "Please enter both phone number and amount")
            return
            
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
            
        # Clear form
        self.phone_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.phone_entry.focus()
        
        # Send to parent for processing
        self.stk_callback(phone, amount)
        
    def add_history(self, message):
        """Add an entry to the history log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.history.insert("1.0", f"[{timestamp}] {message}\n")
        self.history.see("1.0")