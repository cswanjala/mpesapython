import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
from dotenv import load_dotenv
from .components import Card, ModernButton, FONT_FAMILY, FONT_SIZE, TEXT_PRIMARY, SURFACE, LIGHT
from config import CONSUMER_KEY, CONSUMER_SECRET, PASSKEY, CALLBACK_URL, SHORTCODE

class Settings(Card):
    """Settings page for API credentials and C2B URL registration"""
    def __init__(self, parent):
        super().__init__(parent)
        
        # Statistics section
        items = [
            ("Total Transactions", "0"),
            ("Successful", "0"),
            ("Failed", "0"),
            ("Total Amount", "KES 0")
        ]
        
        self.add_title("Statistics")
        stats_frame = tk.Frame(self.content, bg=SURFACE)
        stats_frame.pack(fill="x", padx=20)
        
        for label, value in items:
            row = tk.Frame(stats_frame, bg=SURFACE)
            row.pack(fill="x", pady=6)
            tk.Label(row, text=label, font=(FONT_FAMILY, FONT_SIZE, "bold"),
                    fg=TEXT_PRIMARY, bg=SURFACE).pack(side="left")
            tk.Label(row, text=value, font=(FONT_FAMILY, FONT_SIZE),
                    fg=TEXT_PRIMARY, bg=SURFACE).pack(side="right")

        # C2B URL Registration Section
        self._create_c2b_section()
        
        # Credentials Section
        self._create_credentials_section()
        
    def _create_c2b_section(self):
        self.add_title("Register C2B URLs", pady=(30, 10))
        
        c2b_frame = tk.Frame(self.content, bg=SURFACE)
        c2b_frame.pack(fill="x", padx=20, pady=20)
        
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
        
    def _create_credentials_section(self):
        cred_frame = tk.Frame(self.content, bg=SURFACE)
        cred_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Consumer Key
        row_ck = tk.Frame(cred_frame, bg=SURFACE)
        row_ck.pack(fill="x", pady=6)
        tk.Label(row_ck, text="Consumer Key:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                 fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.consumer_entry = tk.Entry(row_ck, font=(FONT_FAMILY, FONT_SIZE+1), relief="solid", bd=1, bg=LIGHT)
        if CONSUMER_KEY:
            self.consumer_entry.insert(0, CONSUMER_KEY)
        self.consumer_entry.pack(side="left", fill="x", expand=True, ipady=4)

        # Consumer Secret
        row_cs = tk.Frame(cred_frame, bg=SURFACE)
        row_cs.pack(fill="x", pady=6)
        tk.Label(row_cs, text="Consumer Secret:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                 fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.consumer_secret_entry = tk.Entry(row_cs, font=(FONT_FAMILY, FONT_SIZE+1), relief="solid", bd=1, bg=LIGHT)
        if CONSUMER_SECRET:
            self.consumer_secret_entry.insert(0, CONSUMER_SECRET)
        self.consumer_secret_entry.pack(side="left", fill="x", expand=True, ipady=4)

        # Passkey
        row_pk = tk.Frame(cred_frame, bg=SURFACE)
        row_pk.pack(fill="x", pady=6)
        tk.Label(row_pk, text="Passkey:", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                 fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
        self.passkey_entry = tk.Entry(row_pk, font=(FONT_FAMILY, FONT_SIZE+1), relief="solid", bd=1, bg=LIGHT)
        if PASSKEY:
            self.passkey_entry.insert(0, PASSKEY)
        self.passkey_entry.pack(side="left", fill="x", expand=True, ipady=4)

        # STK Callback URL
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
                from mpesa_client import register_c2b_urls
                result = register_c2b_urls(
                    shortcode=shortcode,
                    confirmation_url=confirmation_url,
                    validation_url=validation_url,
                    response_type=response_type
                )
                
                def on_complete():
                    self.register_btn.config(state="normal", text="Register URLs")
                    if isinstance(result, Exception):
                        messagebox.showerror("Error", str(result))
                    else:
                        messagebox.showinfo("Success", "URLs registered successfully")
                
                self.after(0, on_complete)
                
            except Exception as e:
                def on_error():
                    self.register_btn.config(state="normal", text="Register URLs")
                    messagebox.showerror("Error", str(e))
                self.after(0, on_error)
                
        threading.Thread(target=worker, daemon=True).start()
        
    def save_credentials(self):
        """Save credentials to .env file"""
        self.save_btn.config(state='disabled', text='Saving...')
        
        def worker():
            try:
                env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
                
                # Read existing env
                env_vars = {}
                if os.path.exists(env_path):
                    load_dotenv(env_path)
                    with open(env_path) as f:
                        for line in f:
                            if '=' in line and not line.startswith('#'):
                                key, value = line.strip().split('=', 1)
                                env_vars[key] = value
                                
                # Update with new values
                updates = {
                    'CONSUMER_KEY': self.consumer_entry.get().strip(),
                    'CONSUMER_SECRET': self.consumer_secret_entry.get().strip(),
                    'PASSKEY': self.passkey_entry.get().strip(),
                    'CALLBACK_URL': self.stk_callback_entry.get().strip(),
                    'SHORTCODE': self.shortcode_entry.get().strip()
                }
                
                env_vars.update(updates)
                
                # Write back to file
                with open(env_path, 'w') as f:
                    for key, value in env_vars.items():
                        f.write(f"{key}={value}\n")
                        
                def on_success():
                    self.save_btn.config(state='normal', text='Save Credentials')
                    messagebox.showinfo('Success', 'Credentials saved')
                    
                self.after(0, on_success)
                
                # Reload config
                load_dotenv(env_path)
                
            except Exception as e:
                def on_error():
                    self.save_btn.config(state='normal', text='Save Credentials')
                    messagebox.showerror('Error', f'Failed to save credentials: {e}')
                self.after(0, on_error)
                
        threading.Thread(target=worker, daemon=True).start()