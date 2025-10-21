import tkinter as tk
from tkinter import ttk, messagebox
import requests
import base64
from datetime import datetime
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class MPesaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("M-Pesa STK Push")
        self.root.geometry("400x500")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Phone number input
        ttk.Label(main_frame, text="Phone Number:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.phone_var = tk.StringVar()
        self.phone_entry = ttk.Entry(main_frame, textvariable=self.phone_var)
        self.phone_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(main_frame, text="Format: 254XXXXXXXXX").grid(row=2, column=0, sticky=tk.W)
        
        # Amount input
        ttk.Label(main_frame, text="Amount (KES):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(main_frame, textvariable=self.amount_var)
        self.amount_entry.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Send button
        self.send_button = ttk.Button(main_frame, text="Send STK Push", command=self.send_stk_push)
        self.send_button.grid(row=5, column=0, pady=20)
        
        # Transaction history
        ttk.Label(main_frame, text="Transaction History:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.history_text = tk.Text(main_frame, height=10, width=40)
        self.history_text.grid(row=7, column=0, pady=5)
        
        # Configure grid
        main_frame.columnconfigure(0, weight=1)
        
    def get_access_token(self):
        """Get OAuth access token from M-Pesa"""
        consumer_key = os.getenv('CONSUMER_KEY')
        consumer_secret = os.getenv('CONSUMER_SECRET')
        
        auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        
        # Create auth string and encode it
        auth_string = f"{consumer_key}:{consumer_secret}"
        base64_auth = base64.b64encode(auth_string.encode()).decode('utf-8')
        
        headers = {
            "Authorization": f"Basic {base64_auth}"
        }
        
        try:
            response = requests.get(auth_url, headers=headers)
            response.raise_for_status()
            return response.json()['access_token']
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get access token: {str(e)}")
            return None
            
    def send_stk_push(self):
        """Send STK push to user's phone"""
        phone = self.phone_var.get().strip()
        amount = self.amount_var.get().strip()
        
        # Validate inputs
        if not phone or not amount:
            messagebox.showerror("Error", "Please fill in both phone number and amount")
            return
            
        try:
            amount = int(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
            
        # Get access token
        access_token = self.get_access_token()
        if not access_token:
            return
            
        # Prepare STK Push request
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        shortcode = os.getenv('SHORTCODE')
        passkey = os.getenv('PASSKEY')
        
        password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode('utf-8')
        
        stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": shortcode,
            "PhoneNumber": phone,
            "CallBackURL": os.getenv('CALLBACK_URL'),
            "AccountReference": "Test",
            "TransactionDesc": "Test Payment"
        }
        
        try:
            response = requests.post(stk_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get('ResponseCode') == "0":
                # Add to transaction history
                self.add_to_history(f"STK Push sent to {phone} for KES {amount}")
                messagebox.showinfo("Success", "STK Push sent successfully!")
            else:
                messagebox.showerror("Error", f"Failed to send STK Push: {result.get('ResponseDescription')}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send STK Push: {str(e)}")
            
    def add_to_history(self, message):
        """Add a message to the transaction history"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.history_text.insert('1.0', f"[{timestamp}] {message}\n")
        
if __name__ == '__main__':
    root = tk.Tk()
    app = MPesaApp(root)
    root.mainloop()