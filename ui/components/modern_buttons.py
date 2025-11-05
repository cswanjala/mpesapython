from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt

class ModernButton(QPushButton):
    def __init__(self, text, primary=False, size="medium"):
        super().__init__(text)
        
        sizes = {
            "small": "padding: 6px 12px; font-size: 12px;",
            "medium": "padding: 8px 16px; font-size: 14px;",
            "large": "padding: 12px 24px; font-size: 16px;"
        }
        
        base_style = """
            QPushButton {
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                margin-top: -1px;
            }
            QPushButton:pressed {
                margin-top: 1px;
            }
        """
        
        if primary:
            self.setStyleSheet(base_style + sizes[size] + """
                QPushButton {
                    background-color: #000000;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #111111;
                }
                QPushButton:disabled {
                    background-color: #3f3f3f;
                    color: #d1d5db;
                }
            """)
        else:
            self.setStyleSheet(base_style + sizes[size] + """
                QPushButton {
                    background-color: #f8fafc;
                    color: #334155;
                    border: 1px solid #e2e8f0;
                }
                QPushButton:hover {
                    background-color: #f1f5f9;
                    border-color: #cbd5e1;
                }
                QPushButton:disabled {
                    background-color: #f8fafc;
                    color: #94a3b8;
                }
            """)
        # Ensure a reasonable minimum height so buttons are visually obvious
        if size == 'large':
            self.setMinimumHeight(44)
        elif size == 'medium':
            self.setMinimumHeight(36)
        else:
            self.setMinimumHeight(28)

        # Small top margin so button doesn't visually merge with form fields
        existing = self.styleSheet()
        self.setStyleSheet(existing + "\nQPushButton { margin-top: 8px; }")

        self.setCursor(Qt.CursorShape.PointingHandCursor)