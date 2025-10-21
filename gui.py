import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        title.pack(anchor="w", padx=20, pady=(20, 10), **kwargs)
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
        
        # Send button
        self.send_btn = ModernButton(form, "Send STK Push", self.send_stk, "primary")
        self.send_btn.pack()
        
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

class Settings(Card):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="x", padx=20, pady=10)
        
        self.add_title("Settings")
        
        # Environment info
        info_frame = tk.Frame(self.content, bg=SURFACE)
        info_frame.pack(fill="x", padx=20, pady=20)
        
        items = [
            ("STK Callback URL", os.getenv('CALLBACK_URL', 'Not set')),
            ("C2B Callback URL", os.getenv('C2B_CALLBACK_URL', 'Not set')),
            ("Consumer Key", os.getenv('CONSUMER_KEY', 'Not set')[:10] + "..." if os.getenv('CONSUMER_KEY') else 'Not set'),
            ("Consumer Secret", os.getenv('CONSUMER_SECRET', 'Not set')[:10] + "..." if os.getenv('CONSUMER_SECRET') else 'Not set')
        ]
        
        for label, value in items:
            row = tk.Frame(info_frame, bg=SURFACE)
            row.pack(fill="x", pady=8)
            
            tk.Label(row, text=label + ":", font=(FONT_FAMILY, FONT_SIZE, "bold"),
                    fg=TEXT_PRIMARY, bg=SURFACE, width=20, anchor="w").pack(side="left")
            tk.Label(row, text=value, fg=TEXT_SECONDARY, bg=SURFACE,
                    anchor="w", wraplength=400).pack(side="left", fill="x", expand=True)

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
        print(f"STK Push: {phone} - KES {amount} [{timestamp}]")
        # Add to transactions table here in real implementation

if __name__ == "__main__":
    app = MpesaManager()
    app.mainloop()