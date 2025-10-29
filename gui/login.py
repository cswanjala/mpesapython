import tkinter as tk
from tkinter import ttk, messagebox
import threading
from .components import Card, ModernButton, FONT_FAMILY, FONT_SIZE, TEXT_PRIMARY, SURFACE, LIGHT, TEXT_SECONDARY

# Import constants from config
from config import LOGIN_URL, SERVER_URL, WEBSOCKET_URL, SHOP_MAP

class LoginPage(Card):
    """Login/Connect page for merchants to authenticate and receive notifications"""
    def __init__(self, parent, manager):
        super().__init__(parent)
        self.pack(fill="x", padx=20, pady=10)
        self.manager = manager

        self.add_title("Connect / Login")
        self._create_form()
        
    def _create_form(self):
        # Container frame inside the card
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

        # Shop selector
        shop_row = tk.Frame(frame, bg=SURFACE)
        shop_row.pack(fill="x", pady=8)
        tk.Label(shop_row, text="Shop:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                 fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.shop_combo = ttk.Combobox(shop_row, values=list(SHOP_MAP.keys()), state='readonly', font=(FONT_FAMILY, FONT_SIZE))
        try:
            self.shop_combo.set(list(SHOP_MAP.keys())[0])
        except Exception:
            pass
        self.shop_combo.pack(side="left", fill="x", expand=True, ipady=4)

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

    def on_connect(self):
        server = self.server_entry.get().rstrip('/')
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        # Selected shop code (BusinessShortCode) if provided
        try:
            shop_name = self.shop_combo.get().strip()
            shop_codes = SHOP_MAP.get(shop_name)
            # Normalize to a list of strings or None
            if isinstance(shop_codes, (list, tuple)):
                shop_codes = [str(s) for s in shop_codes]
            elif shop_codes is not None:
                shop_codes = [str(shop_codes)]
            else:
                shop_codes = None
        except Exception:
            shop_codes = None

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
                    # Note: Implement login logic here if needed
                    pass
                except Exception:
                    pass

                # Start socket.io client (pass server base URL)
                ws_url = WEBSOCKET_URL or server
                # Pass selected shop_code so server-side can filter/join appropriate room
                try:
                    self.manager.start_ws_client(ws_url, token, merchant_id, shop_codes)
                except TypeError:
                    self.manager.start_ws_client(ws_url)

                def on_success():
                    self.connect_btn.config(state='normal', text='Connect')
                    # Update sidebar highlight
                    self.manager.switch_page('dashboard')
                    # Store current shop code for filtering notifications
                    try:
                        self.manager._current_shop_codes = shop_codes
                    except Exception:
                        pass
                    # Store server base URL (HTTP) so transactions can be fetched
                    try:
                        self.manager._server_url = server
                    except Exception:
                        pass
                    messagebox.showinfo('Connected', 'Connected to server for notifications')
                self.manager.after(0, on_success)

            except Exception as e:
                error_message = str(e)
                def on_err(message=error_message):
                    self.connect_btn.config(state='normal', text='Connect')
                    messagebox.showerror('Connection Error', message)
                self.manager.after(0, on_err)

        threading.Thread(target=worker, daemon=True).start()