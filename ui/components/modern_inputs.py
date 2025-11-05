from PyQt6.QtWidgets import QLineEdit, QComboBox
from PyQt6.QtCore import Qt

class ModernLineEdit(QLineEdit):
    def __init__(self, placeholder="", password=False):
        super().__init__()
        self.setPlaceholderText(placeholder)
        
        if password:
            self.setEchoMode(QLineEdit.EchoMode.Password)
            
        self.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
                color: #0f172a;
                selection-background-color: #dbeafe;
            }
            QLineEdit:focus {
                border-color: #2563eb;
                outline: none;
            }
            QLineEdit:hover {
                border-color: #cbd5e1;
            }
            QLineEdit::placeholder {
                color: #94a3b8;
            }
        """)


class ModernComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #cbd5e1;
            }
            QComboBox:focus {
                border-color: #2563eb;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #64748b;
                width: 0px;
                height: 0px;
            }
        """)