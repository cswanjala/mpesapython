import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import traceback
import os
from dotenv import load_dotenv
import requests
import base64
import threading
from config import CONSUMER_KEY, CONSUMER_SECRET, SHORTCODE, PASSKEY, CALLBACK_URL, C2B_CALLBACK_URL, SERVER_URL, LOGIN_URL, WEBSOCKET_URL, get
import mpesa_client
import importlib
import config

# Ensure .env loaded by config.py already

# Modern Color Palette
PRIMARY = "#2563eb"
SECONDARY = "#1e40af"
SUCCESS = "#10b981"
DANGER = "#ef4444"
WARNING = "#f59e0b"
DARK = "#1f2937"
LIGHT = "#f8fafc"
SURFACE = "#ffffff"
SURFACE_VARIANT = "#f1f5f9"
BORDER = "#e2e8f0"
TEXT_PRIMARY = "#0f172a"
TEXT_SECONDARY = "#64748b"
SHADOW = "#e2e8f0"

FONT_FAMILY = "Segoe UI"
FONT_SIZE = 10

class ModernButton(tk.Button):
    """Modern styled button with hover effects"""
    def __init__(self, parent, text, command=None, style="primary", **kwargs):
        self.style = style
        self.base_bg = {
            "primary": PRIMARY,
            "secondary": SECONDARY,
            "success": SUCCESS,
            "danger": DANGER
        }[style]
        
        self.hover_bg = {
            "primary": "#1d4ed8",
            "secondary": "#1e40af",
            "success": "#059669",
            "danger": "#dc2626"
        }[style]
        
        super().__init__(parent, text=text, command=command, 
                        bg=self.base_bg, fg="white", 
                        font=(FONT_FAMILY, FONT_SIZE, "bold"),
                        relief="flat", bd=0, padx=24, pady=8,
                        cursor="hand2", **kwargs)
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
    def on_enter(self, e):
        self.config(bg=self.hover_bg)
        
    def on_leave(self, e):
        self.config(bg=self.base_bg)

class Card(tk.Frame):
    """Modern card component with REAL shadow effect"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Create shadow effect using multiple frames
        self.create_shadow()
        
        # Main card content
        self.content = tk.Frame(self, bg=SURFACE, relief="flat", bd=0)
        self.content.pack(fill="both", expand=True)
        
    def create_shadow(self):
        """Create a realistic shadow effect"""
        # Shadow frames (offset to create depth)
        shadow1 = tk.Frame(self, bg="#f0f0f0", relief="flat", bd=0)
        shadow1.place(x=2, y=2, relwidth=1, relheight=1)
        
        shadow2 = tk.Frame(self, bg="#e0e0e0", relief="flat", bd=0)
        shadow2.place(x=1, y=1, relwidth=1, relheight=1)
        
        # Main card on top
        self.main_card = tk.Frame(self, bg=SURFACE, relief="solid", bd=1)
        self.main_card.place(relwidth=1, relheight=1)
        
        # Move content to main_card
        self.content = self.main_card
        
    def add_title(self, text, **kwargs):
        title = tk.Label(self.content, text=text, font=(FONT_FAMILY, 16, "bold"), 
                        fg=TEXT_PRIMARY, bg=SURFACE)
        # Only use pady from kwargs if provided, otherwise use default
        pack_kwargs = {"anchor": "w", "padx": 20}
        if "pady" not in kwargs:
            pack_kwargs["pady"] = (20, 10)
        pack_kwargs.update(kwargs)
        title.pack(**pack_kwargs)
        return title

class Sidebar(tk.Frame):
    def __init__(self, parent, callback):
        super().__init__(parent, width=280, bg=DARK)
        self.callback = callback
        self.pack(fill="y", side="left")
        self.pack_propagate(False)
        
        # Logo
        logo = tk.Label(self, text="💳 M-Pesa Manager", 
                       font=(FONT_FAMILY, 18, "bold"), fg="white", bg=DARK)
        logo.pack(pady=40, padx=20, anchor="w")
        
        # Navigation items
        nav_items = [
            ("📊", "Dashboard"),
            ("📋", "Transactions"),
            ("🔌", "Connect"),
            ("⚙️", "Settings")
        ]
        
        self.buttons = {}
        for i, (icon, text) in enumerate(nav_items):
            btn = tk.Button(self, text=f"{icon}  {text}", 
                          font=(FONT_FAMILY, FONT_SIZE+1),
                          fg="white", bg=DARK, relief="flat", bd=0,
                          anchor="w", padx=30, pady=15,
                          command=lambda t=text: callback(t.lower()))
            btn.pack(fill="x", pady=2, padx=10)
            
            # Hover effect
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#374151"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=DARK))
            
            self.buttons[text.lower()] = btn

class Dashboard(Card):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.pack(fill="x", padx=20, pady=(20, 10))
        
        self.add_title("Send STK Push")
        
        # Form container
        form = tk.Frame(self.content, bg=SURFACE)
        form.pack(fill="x", padx=20, pady=(0, 20))
        
        # Phone input
        tk.Label(form, text="Phone Number", font=(FONT_FAMILY, FONT_SIZE, "bold"), 
                fg=TEXT_PRIMARY, bg=SURFACE).pack(anchor="w", pady=(20, 5))
        self.phone_entry = tk.Entry(form, font=(FONT_FAMILY, FONT_SIZE+1), 
                                   relief="solid", bd=1, bg=LIGHT)
        self.phone_entry.pack(fill="x", pady=(0, 15), ipady=8)
        
        # Amount input
        tk.Label(form, text="Amount (KES)", font=(FONT_FAMILY, FONT_SIZE, "bold"), 
                fg=TEXT_PRIMARY, bg=SURFACE).pack(anchor="w", pady=(0, 5))
        self.amount_entry = tk.Entry(form, font=(FONT_FAMILY, FONT_SIZE+1), 
                                    relief="solid", bd=1, bg=LIGHT)
        self.amount_entry.pack(fill="x", pady=(0, 20), ipady=8)
        
        # Buttons row (Send + Test)
        btn_row = tk.Frame(form, bg=SURFACE)
        btn_row.pack(pady=(0, 10))

        self.send_btn = ModernButton(btn_row, "Send STK Push", self.send_stk, "primary")
        self.send_btn.pack(side="left", padx=(0, 8))

    # removed Test STK button per request

        # Stats cards
        self.add_stats()

    def add_stats(self):
        """Add statistics cards"""
        stats_frame = tk.Frame(self.content, bg=SURFACE)
        stats_frame.pack(fill="x", padx=20, pady=(20, 0))
        
        stats = [
            ("Total Sent", "KES 45,230", SUCCESS),
            ("Today's Tx", "12", PRIMARY),
            ("Success Rate", "98%", WARNING)
        ]
        
        for i, (label, value, color) in enumerate(stats):
            col = i % 3
            stat_card = tk.Frame(stats_frame, bg=SURFACE_VARIANT, relief="solid", bd=1)
            stat_card.grid(row=0, column=col, padx=10, pady=10, sticky="ew")
            
            tk.Label(stat_card, text=value, font=(FONT_FAMILY, 24, "bold"), 
                    fg=color, bg=SURFACE_VARIANT).pack(pady=10)
            tk.Label(stat_card, text=label, font=(FONT_FAMILY, FONT_SIZE), 
                    fg=TEXT_SECONDARY, bg=SURFACE_VARIANT).pack()

        # Simple history list
        hist_frame = tk.Frame(self.content, bg=SURFACE)
        hist_frame.pack(fill="x", padx=20, pady=(10, 20))
        tk.Label(hist_frame, text="Activity", font=(FONT_FAMILY, FONT_SIZE, "bold"), fg=TEXT_PRIMARY, bg=SURFACE).pack(anchor="w")
        self.history_list = tk.Listbox(hist_frame, height=4, bg=SURFACE, bd=0, fg=TEXT_SECONDARY)
        self.history_list.pack(fill="x", pady=(6, 0))

    def add_history(self, text):
        try:
            t = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' — ' + str(text)
            # keep last 50
            if hasattr(self, 'history_list'):
                self.history_list.insert(0, t)
                if self.history_list.size() > 50:
                    self.history_list.delete(50, 'end')
        except Exception:
            pass

    def send_stk(self):
        phone = self.phone_entry.get().strip()
        amount = self.amount_entry.get().strip()
        
        if not phone or not amount:
            messagebox.showerror("Error", "Please fill all fields")
            return
            
        try:
            amount_int = int(amount)
            if amount_int <= 0:
                raise ValueError("Amount must be greater than 0")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        
        self.callback(phone, amount_int)
        messagebox.showinfo("Success", f"STK Push sent to {phone} for KES {amount}")

        

class Transactions(Card):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.add_title("Recent Transactions")
        
        # Create treeview container
        tree_frame = tk.Frame(self.content)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(20, 10))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Treeview with modern styling
        columns = ("Time", "Amount", "Phone", "Status", "TX ID")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="w")
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Grid
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        # Sample data
        sample_data = [
            ("2025-10-21 14:23", "1,500", "254712345678", "✅ Success", "MP123456789"),
            ("2025-10-21 13:45", "2,300", "254798765432", "✅ Success", "MP987654321"),
            ("2025-10-21 12:10", "800", "254700111222", "❌ Failed", "MP555666777"),
            ("2025-10-20 18:30", "1,200", "254733344555", "✅ Success", "MP444555666")
        ]
        
        for item in sample_data:
            self.tree.insert("", "end", values=item)

    def add_transaction(self, time, amount, phone, status, txid):
        """Utility to add a transaction row from external events"""
        self.tree.insert("", 0, values=(time, amount, phone, status, txid))

class Settings(Card):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="x", padx=20, pady=10)
        
        self.add_title("Settings")
        
        # Environment info
        info_frame = tk.Frame(self.content, bg=SURFACE)
        info_frame.pack(fill="x", padx=20, pady=20)
        
        items = [
            ("STK Callback URL", CALLBACK_URL or 'Not set'),
            ("C2B Callback URL", C2B_CALLBACK_URL or 'Not set'),
            ("Consumer Key", (CONSUMER_KEY[:10] + '...') if CONSUMER_KEY else 'Not set'),
            ("Consumer Secret", (CONSUMER_SECRET[:10] + '...') if CONSUMER_SECRET else 'Not set')
        ]
        
        for label, value in items:
            row = tk.Frame(info_frame, bg=SURFACE)
            row.pack(fill="x", pady=8)
            
            tk.Label(row, text=label + ":", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                    fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
            tk.Label(row, text=value, fg=TEXT_SECONDARY, bg=SURFACE,
                    anchor="w", wraplength=400).pack(side="left", fill="x", expand=True)

        # C2B URL Registration Section
        self.add_title("Register C2B URLs", pady=(30, 10))
        
        c2b_frame = tk.Frame(self.content, bg=SURFACE)
        c2b_frame.pack(fill="x", padx=20, pady=20)

        # Credentials editing area (consumer keys, passkey, callback)
        cred_frame = tk.Frame(self.content, bg=SURFACE)
        cred_frame.pack(fill="x", padx=20, pady=(0, 10))

        row_ck = tk.Frame(cred_frame, bg=SURFACE)
        row_ck.pack(fill="x", pady=6)
        tk.Label(row_ck, text="Consumer Key:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                 fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.consumer_entry = tk.Entry(row_ck, font=(FONT_FAMILY, FONT_SIZE+1), relief="solid", bd=1, bg=LIGHT)
        if CONSUMER_KEY:
            self.consumer_entry.insert(0, CONSUMER_KEY)
        self.consumer_entry.pack(side="left", fill="x", expand=True, ipady=4)

        row_cs = tk.Frame(cred_frame, bg=SURFACE)
        row_cs.pack(fill="x", pady=6)
        tk.Label(row_cs, text="Consumer Secret:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                 fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.consumer_secret_entry = tk.Entry(row_cs, font=(FONT_FAMILY, FONT_SIZE+1), relief="solid", bd=1, bg=LIGHT)
        if CONSUMER_SECRET:
            self.consumer_secret_entry.insert(0, CONSUMER_SECRET)
        self.consumer_secret_entry.pack(side="left", fill="x", expand=True, ipady=4)

        row_pk = tk.Frame(cred_frame, bg=SURFACE)
        row_pk.pack(fill="x", pady=6)
        tk.Label(row_pk, text="Passkey:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                 fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.passkey_entry = tk.Entry(row_pk, font=(FONT_FAMILY, FONT_SIZE+1), relief="solid", bd=1, bg=LIGHT)
        if PASSKEY:
            self.passkey_entry.insert(0, PASSKEY)
        self.passkey_entry.pack(side="left", fill="x", expand=True, ipady=4)

        row_cb = tk.Frame(cred_frame, bg=SURFACE)
        row_cb.pack(fill="x", pady=6)
        tk.Label(row_cb, text="STK Callback URL:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                 fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.stk_callback_entry = tk.Entry(row_cb, font=(FONT_FAMILY, FONT_SIZE+1), relief="solid", bd=1, bg=LIGHT)
        if CALLBACK_URL:
            self.stk_callback_entry.insert(0, CALLBACK_URL)
        self.stk_callback_entry.pack(side="left", fill="x", expand=True, ipady=4)

        # Save credentials button
        save_row = tk.Frame(cred_frame, bg=SURFACE)
        save_row.pack(fill="x", pady=(10, 0))
        self.save_btn = ModernButton(save_row, "Save Credentials", self.save_credentials, "secondary")
        self.save_btn.pack(side="left")
        
        # Shortcode input
        shortcode_row = tk.Frame(c2b_frame, bg=SURFACE)
        shortcode_row.pack(fill="x", pady=8)
        tk.Label(shortcode_row, text="Shortcode:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.shortcode_entry = tk.Entry(shortcode_row, font=(FONT_FAMILY, FONT_SIZE+1),
                                      relief="solid", bd=1, bg=LIGHT)
        self.shortcode_entry.insert(0, SHORTCODE or '')
        self.shortcode_entry.pack(side="left", fill="x", expand=True, ipady=4)
        
        # Validation URL input
        validation_row = tk.Frame(c2b_frame, bg=SURFACE)
        validation_row.pack(fill="x", pady=8)
        tk.Label(validation_row, text="Validation URL:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.validation_entry = tk.Entry(validation_row, font=(FONT_FAMILY, FONT_SIZE+1),
                                       relief="solid", bd=1, bg=LIGHT)
        self.validation_entry.pack(side="left", fill="x", expand=True, ipady=4)
        
        # Confirmation URL input
        confirmation_row = tk.Frame(c2b_frame, bg=SURFACE)
        confirmation_row.pack(fill="x", pady=8)
        tk.Label(confirmation_row, text="Confirmation URL:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.confirmation_entry = tk.Entry(confirmation_row, font=(FONT_FAMILY, FONT_SIZE+1),
                                         relief="solid", bd=1, bg=LIGHT)
        self.confirmation_entry.pack(side="left", fill="x", expand=True, ipady=4)
        
        # Response Type
        response_row = tk.Frame(c2b_frame, bg=SURFACE)
        response_row.pack(fill="x", pady=8)
        tk.Label(response_row, text="Response Type:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.response_type = ttk.Combobox(response_row, values=["Completed", "Cancelled"], 
                                         state="readonly", font=(FONT_FAMILY, FONT_SIZE))
        self.response_type.set("Completed")
        self.response_type.pack(side="left", fill="x", expand=True, ipady=4)
        
        # Register button
        button_row = tk.Frame(c2b_frame, bg=SURFACE)
        button_row.pack(fill="x", pady=(20, 0))
        self.register_btn = ModernButton(button_row, "Register URLs", self.register_urls, "primary")
        self.register_btn.pack()
        
    def register_urls(self):
        """Register C2B URLs with M-Pesa"""
        shortcode = self.shortcode_entry.get().strip()
        validation_url = self.validation_entry.get().strip()
        confirmation_url = self.confirmation_entry.get().strip()
        response_type = self.response_type.get()
        
        if not all([shortcode, validation_url, confirmation_url]):
            messagebox.showerror("Error", "Please fill all fields")
            return
            
        # Show busy state
        self.register_btn.config(state="disabled", text="Registering...")
        self.update()
        
        def worker():
            try:
                # Get access token
                consumer_key = CONSUMER_KEY
                consumer_secret = CONSUMER_SECRET
                if not consumer_key or not consumer_secret:
                    raise RuntimeError('Missing CONSUMER_KEY or CONSUMER_SECRET in config/.env')

                auth_str = f"{consumer_key}:{consumer_secret}"
                b64 = base64.b64encode(auth_str.encode()).decode()
                auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
                headers = {'Authorization': f'Basic {b64}'}
                r = requests.get(auth_url, headers=headers, timeout=10)
                r = requests.get(auth_url, headers=headers, timeout=10)
                try:
                    r.raise_for_status()
                except Exception as ex:
                    body = getattr(r, 'text', '')
                    raise RuntimeError(f'Auth token request failed: {ex} - response: {body}')
                token = r.json().get('access_token')
                if not token:
                    raise RuntimeError('Failed to obtain access token')

                # Register URLs
                register_url = 'https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl'
                payload = {
                    'ShortCode': shortcode,
                    'ResponseType': response_type,
                    'ConfirmationURL': confirmation_url,
                    'ValidationURL': validation_url
                }
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                resp = requests.post(register_url, json=payload, headers=headers, timeout=15)
                resp.raise_for_status()
                data = resp.json()

                def on_success():
                            consumer_key = CONSUMER_KEY
                            consumer_secret = CONSUMER_SECRET
                            if not consumer_key or not consumer_secret:
                                raise RuntimeError('Missing CONSUMER_KEY or CONSUMER_SECRET in config/.env')
            except Exception as e:
                def on_error():
                    self.register_btn.config(state="normal", text="Register URLs")
                    messagebox.showerror('Registration Error', str(e))
                self.after(0, on_error)

        threading.Thread(target=worker, daemon=True).start()

    def save_credentials(self):
        """Persist entered credentials to .env and reload config at runtime."""
        # Disable to prevent double clicks
        self.save_btn.config(state='disabled', text='Saving...')

        def worker():
            try:
                # Collect values
                ck = self.consumer_entry.get().strip()
                cs = self.consumer_secret_entry.get().strip()
                pk = self.passkey_entry.get().strip()
                cb = self.stk_callback_entry.get().strip()

                env_path = os.path.join(os.path.dirname(__file__), '.env')
                lines = []
                if os.path.exists(env_path):
                    with open(env_path, 'r', encoding='utf-8') as f:
                        lines = f.read().splitlines()

                def set_key(lines, key, val):
                    key_eq = key + '='
                    found = False
                    for i, line in enumerate(lines):
                        if line.strip().startswith(key_eq):
                            lines[i] = f"{key}={val}"
                            found = True
                            break
                    if not found:
                        lines.append(f"{key}={val}")
                    return lines

                if ck:
                    lines = set_key(lines, 'CONSUMER_KEY', ck)
                if cs:
                    lines = set_key(lines, 'CONSUMER_SECRET', cs)
                if pk:
                    lines = set_key(lines, 'PASSKEY', pk)
                if cb:
                    lines = set_key(lines, 'CALLBACK_URL', cb)

                # Also if SHORTCODE field exists elsewhere in settings, preserve it
                sc = getattr(self, 'shortcode_entry', None)
                if sc:
                    scv = sc.get().strip()
                    if scv:
                        lines = set_key(lines, 'SHORTCODE', scv)

                # Write back
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines) + '\n')

                # Reload config module so new values take effect
                try:
                    importlib.reload(config)
                except Exception:
                    pass

                # Update mpesa_client module if it reads config at import
                try:
                    importlib.reload(mpesa_client)
                except Exception:
                    pass

                def on_done():
                    self.save_btn.config(state='normal', text='Save Credentials')
                    messagebox.showinfo('Saved', 'Credentials saved to .env and reloaded')
                self.after(0, on_done)

            except Exception as e:
                def on_err():
                    self.save_btn.config(state='normal', text='Save Credentials')
                    messagebox.showerror('Save Error', str(e))
                self.after(0, on_err)

        threading.Thread(target=worker, daemon=True).start()


class LoginPage(Card):
    """Login/Connect page for merchants to authenticate and receive notifications"""
    def __init__(self, parent, manager):
        super().__init__(parent)
        self.pack(fill="x", padx=20, pady=10)

        self.add_title("Connect / Login")

        # container frame inside the card
        frame = tk.Frame(self.content, bg=SURFACE)
        frame.pack(fill="x", padx=20, pady=10)

        # Server URL (optional override)
        row = tk.Frame(frame, bg=SURFACE)
        row.pack(fill="x", pady=8)
        tk.Label(row, text="Server URL:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                 fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.server_entry = tk.Entry(row, font=(FONT_FAMILY, FONT_SIZE+1), relief="solid", bd=1, bg=LIGHT)
        self.server_entry.insert(0, SERVER_URL or 'http://localhost:5000')
        self.server_entry.pack(side="left", fill="x", expand=True, ipady=4)

        # Username / merchant id
        row2 = tk.Frame(frame, bg=SURFACE)
        row2.pack(fill="x", pady=8)
        tk.Label(row2, text="Merchant ID / Username:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                 fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.username_entry = tk.Entry(row2, font=(FONT_FAMILY, FONT_SIZE+1), relief="solid", bd=1, bg=LIGHT)
        self.username_entry.pack(side="left", fill="x", expand=True, ipady=4)

        # Password (optional)
        row3 = tk.Frame(frame, bg=SURFACE)
        row3.pack(fill="x", pady=8)
        tk.Label(row3, text="Password (optional):", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                 fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.password_entry = tk.Entry(row3, font=(FONT_FAMILY, FONT_SIZE+1), relief="solid", bd=1, bg=LIGHT, show="*")
        self.password_entry.pack(side="left", fill="x", expand=True, ipady=4)

        # Connect button
        btn_row = tk.Frame(frame, bg=SURFACE)
        btn_row.pack(fill="x", pady=(20, 0))
        self.connect_btn = ModernButton(btn_row, "Connect", self.on_connect, "primary")
        self.connect_btn.pack()

        # Status
        self.status_label = tk.Label(self.content, text="Not connected", fg=TEXT_SECONDARY, bg=SURFACE)
        self.status_label.pack(anchor="w", padx=20, pady=(10, 0))

        # keep reference to manager
        self.manager = manager

    def on_connect(self):
        server = self.server_entry.get().rstrip('/')
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username:
            messagebox.showerror('Error', 'Please enter your Merchant ID / username')
            return

        # Disable UI while connecting
        self.connect_btn.config(state='disabled', text='Connecting...')

        def worker():
            try:
                # Try login endpoint if provided
                login_url = LOGIN_URL or f"{server}/api/login"
                token = None
                merchant_id = username

                try:
                    resp = requests.post(login_url, json={'username': username, 'password': password}, timeout=8)
                    if resp.status_code == 200:
                        j = resp.json()
                        token = j.get('token') or j.get('access_token')
                        merchant_id = j.get('merchant_id') or merchant_id
                except Exception:
                    # If login fails, we'll proceed with username only (server may accept ws query param)
                    token = None

                # Start socket.io client (pass server base URL)
                ws_url = WEBSOCKET_URL or server
                self.manager.start_ws_client(ws_url, token, merchant_id)

                def on_success():
                    self.status_label.config(text=f"Connected as {merchant_id}")
                    self.connect_btn.config(state='normal', text='Connect')
                    # Store merchant_id in manager for STK push
                    self.manager._current_merchant_id = merchant_id
                    messagebox.showinfo('Connected', 'Connected to server for notifications')
                self.manager.after(0, on_success)

            except Exception as e:
                def on_err():
                    self.connect_btn.config(state='normal', text='Connect')
                    messagebox.showerror('Connection Error', str(e))
                self.manager.after(0, on_err)

        threading.Thread(target=worker, daemon=True).start()

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
        
        # Add a quick log entry that Send was clicked
        try:
            log_path = os.path.join(os.path.dirname(__file__), 'stk_debug.log')
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"\n[{datetime.utcnow().isoformat()}] Send STK clicked - phone={phone} amount={amount} merchant={merchant_id}\n")
        except Exception:
            pass

        # Send STK push in background to avoid blocking the GUI
        def worker():
            try:
                # Use the reusable client module to perform STK push
                resp = mpesa_client.lipa_na_mpesa_online(phone, int(amount))
                print(resp)
                stk_resp_text = getattr(resp, 'text', '')

                # Log request/response where possible
                try:
                    log_path = os.path.join(os.path.dirname(__file__), 'stk_debug.log')
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write('\n--- STK PUSH RUN ' + datetime.utcnow().isoformat() + ' ---\n')
                        # resp.request may be a PreparedRequest
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
                        f.write('STK RESPONSE TEXT:\n' + stk_resp_text + '\n')
                except Exception:
                    pass

                # Interpret response
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
                    raise RuntimeError(f'STK request failed: {ex} - response: {stk_resp_text}')

                # Update GUI on main thread
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
        # Add to transactions table here in real implementation

        

    # --- WebSocket client for real-time notifications ---
    def start_ws_client(self, ws_url, token=None, merchant_id=None):
        """Start a Socket.IO client to receive server notifications.

        Uses python-socketio client. The server should emit 'notification' events with
        payloads like: {"type": "transaction", "data": {...}}.
        """
        try:
            import socketio
        except Exception:
            messagebox.showerror('Missing Dependency', 'python-socketio is required. Install with: pip install python-socketio')
            return

        # If a client already exists, disconnect it first
        try:
            if hasattr(self, '_sio') and self._sio:
                try:
                    self._sio.disconnect()
                except Exception:
                    pass
        except Exception:
            pass

        self._sio = socketio.Client(reconnection=True, logger=False, engineio_logger=False)

        @self._sio.event
        def connect():
            self.after(0, lambda: messagebox.showinfo('WS', 'Connected to notification server'))
            # Join merchant room if merchant_id provided
            try:
                if merchant_id:
                    self._sio.emit('join', {'merchant_id': merchant_id})
            except Exception:
                pass

        @self._sio.event
        def disconnect():
            self._current_merchant_id = None  # Clear merchant_id on disconnect
            self.after(0, lambda: messagebox.showinfo('WS', 'Disconnected from notification server'))

        @self._sio.on('notification')
        def on_notification(msg):
            try:
                # Expecting payload: {"type":"transaction","data": { ... M-Pesa body ... }}
                if isinstance(msg, dict) and msg.get('type') == 'transaction':
                    d = msg.get('data', {}) or {}

                    # Default display values
                    ttime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    amount = ''
                    phone = ''
                    status = 'Received'
                    txid = ''

                    # If this is an M-Pesa STK callback (nested Body -> stkCallback)
                    try:
                        stk = d.get('Body', {}).get('stkCallback') if isinstance(d, dict) else None
                        if stk:
                            # Result fields
                            res_desc = stk.get('ResultDesc') or ''
                            res_code = stk.get('ResultCode')
                            status = f"{res_desc}" if res_desc else (f"Code {res_code}" if res_code is not None else status)

                            # CheckoutRequestID or MerchantRequestID
                            txid = stk.get('MpesaReceiptNumber') or stk.get('CheckoutRequestID') or stk.get('MerchantRequestID') or ''

                            # CallbackMetadata contains Item list
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
                                    elif name.lower() in ('mpesareceiptnumber', 'mpesareceiptnumber'):
                                        txid = val or txid
                                    elif name.lower() in ('transactiondate',):
                                        try:
                                            s = str(val)
                                            if len(s) >= 14:
                                                ttime = datetime.strptime(s[:14], '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
                                        except Exception:
                                            pass
                            # Fallbacks
                            if not txid:
                                txid = stk.get('MpesaReceiptNumber') or stk.get('CheckoutRequestID') or ''
                    except Exception:
                        # not the expected structure, fallthrough to other handlers
                        pass

                    # Generic flat structure fallback
                    if not amount:
                        amount = d.get('amount') or d.get('Amount') or amount
                    if not phone:
                        phone = d.get('phone') or d.get('PhoneNumber') or phone
                    if not txid:
                        txid = d.get('txid') or d.get('transaction_id') or txid

                    # Add to transactions table
                    tx_page = self.pages.get('transactions')
                    if tx_page:
                        tx_page.add_transaction(ttime, amount, phone, status, txid)

                    # Non-blocking popup with useful info
                    def show_popup():
                        try:
                            title = 'Payment Notification'
                            body = f"Amount: {amount}\nPhone: {phone}\nTX: {txid}\nStatus: {status}"
                            messagebox.showinfo(title, body)
                        except Exception:
                            pass

                    self.after(0, show_popup)
                else:
                    # For other messages, show raw payload
                    self.after(0, lambda: messagebox.showinfo('Notification', str(msg)))
            except Exception as e:
                err = str(e)
                try:
                    self.after(0, lambda err=err: messagebox.showerror('Notification Error', err))
                except Exception:
                    pass

        # Build connect URL (socketio client will add /socket.io if needed)
        connect_params = {}
        if token:
            connect_params['token'] = token
        if merchant_id:
            connect_params['merchant_id'] = merchant_id

        def run_client():
            try:
                # Using query string for token/merchant (server will parse query params)
                qs = '&'.join([f"{k}={v}" for k, v in connect_params.items()])
                url = ws_url
                if qs:
                    url = f"{ws_url}?{qs}"
                self._sio.connect(url, wait=True)
                self._sio.wait()
            except Exception as e:
                err = str(e)
                try:
                    self.after(0, lambda err=err: messagebox.showerror('Connection Error', err))
                except Exception:
                    pass

        self._sio_thread = threading.Thread(target=run_client, daemon=True)
        self._sio_thread.start()

if __name__ == "__main__":
    app = MpesaManager()
    app.mainloop()