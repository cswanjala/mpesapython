import tkinter as tk
from .components import FONT_FAMILY, FONT_SIZE, PRIMARY, SURFACE, TEXT_PRIMARY, WHITE

class Sidebar(tk.Frame):
    """Navigation sidebar with menu buttons"""
    def __init__(self, parent, switch_callback):
        super().__init__(parent, bg=SURFACE, width=200)
        self.pack(side="left", fill="y", padx=10, pady=20)
        self.pack_propagate(False)
        
        # Menu items
        menu_items = [
            ("dashboard", "Dashboard"),
            ("transactions", "Transactions"),
            ("connect", "Connect"),
            ("settings", "Settings")
        ]
        
        self.buttons = {}
        for page_id, label in menu_items:
            btn = tk.Button(
                self,
                text=label,
                font=(FONT_FAMILY, FONT_SIZE),
                fg=TEXT_PRIMARY,
                bg=SURFACE,
                bd=0,
                padx=20,
                pady=10,
                anchor="w",
                cursor="hand2",
                width=20,
                command=lambda p=page_id: switch_callback(p)
            )
            btn.pack(fill="x", pady=2)
            self.buttons[page_id] = btn