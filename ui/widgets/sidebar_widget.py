from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

class SidebarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self.setStyleSheet("""
            SidebarWidget {
                background-color: #1e293b;
                color: white;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(8)
        
        # Logo/Header
        header = QLabel("M-Pesa Manager")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #f8fafc;
            padding: 20px;
            border-bottom: 1px solid #334155;
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Navigation buttons
        self.nav_buttons = {}
        
        nav_items = [
            ("Dashboard", "📊"),
            ("Transactions", "💳"),
            ("Settings", "⚙️"),
            ("Connect", "🔗")
        ]
        
        for text, icon in nav_items:
            btn = QPushButton(f"{icon}  {text}")
            btn.setFixedHeight(44)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #cbd5e1;
                    border: none;
                    text-align: left;
                    padding: 0px 20px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #334155;
                    color: #f8fafc;
                }
                QPushButton:pressed {
                    background-color: #475569;
                }
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(btn)
            self.nav_buttons[text.lower()] = btn
        
        layout.addStretch()
        
        # Status indicator
        status_widget = QWidget()
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(20, 10, 20, 10)
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #ef4444; font-size: 16px;")
        status_label = QLabel("Disconnected")
        status_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        status_widget.setLayout(status_layout)
        
        layout.addWidget(status_widget)
        self.setLayout(layout)
    
    def set_connected(self, connected):
        if connected:
            self.status_indicator.setStyleSheet("color: #10b981; font-size: 16px;")
        else:
            self.status_indicator.setStyleSheet("color: #ef4444; font-size: 16px;")