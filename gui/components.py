import tkinter as tk
from tkinter import ttk

# Constants from original gui.py
FONT_FAMILY = "Segoe UI"
FONT_SIZE = 11
PRIMARY = "#007bff"
SECONDARY = "#6c757d"
SUCCESS = "#28a745"
DANGER = "#dc3545"
WARNING = "#ffc107"
INFO = "#17a2b8"
LIGHT = "#f8f9fa"
DARK = "#343a40"
MUTED = "#6c757d"
WHITE = "#ffffff"
SURFACE = "#ffffff"
TEXT_PRIMARY = "#212529"
TEXT_SECONDARY = "#6c757d"

class Card(tk.Frame):
    """Base card component with title and content sections"""
    def __init__(self, parent):
        super().__init__(parent, bg=SURFACE)
        self.content = tk.Frame(self, bg=SURFACE)
        self.content.pack(fill="both", expand=True)
        
    def add_title(self, text, **kwargs):
        title = tk.Label(self, text=text, font=(FONT_FAMILY, FONT_SIZE+4, "bold"),
                        fg=TEXT_PRIMARY, bg=SURFACE)
        # If pady is in kwargs, don't set it in pack()
        pack_kwargs = {'anchor': "w", 'padx': 20}
        if 'pady' not in kwargs:
            pack_kwargs['pady'] = 10
        title.pack(**pack_kwargs, **kwargs)

class ModernButton(tk.Button):
    """Styled button component with different color variants"""
    def __init__(self, parent, text, command, style="primary"):
        # Map style names to colors
        colors = {
            "primary": PRIMARY,
            "secondary": SECONDARY,
            "success": SUCCESS,
            "danger": DANGER,
            "warning": WARNING,
            "info": INFO
        }
        bg_color = colors.get(style, PRIMARY)
        
        super().__init__(
            parent,
            text=text,
            command=command,
            font=(FONT_FAMILY, FONT_SIZE),
            fg=WHITE,
            bg=bg_color,
            activebackground=bg_color,
            activeforeground=WHITE,
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        
        def on_enter(e):
            self["background"] = colors.get(f"{style}_hover", bg_color)
            
        def on_leave(e):
            self["background"] = bg_color
            
        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)