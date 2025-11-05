import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Set application-wide font
    from PyQt6.QtGui import QFont
    from PyQt6.QtGui import QPalette, QColor
    font = QFont("Segoe UI", 11)
    app.setFont(font)
    # Improve default text contrast for better readability across widgets
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#0f172a"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#0f172a"))
    app.setPalette(palette)
    
    print("[GUI Debug] Starting application with Multi-Desktop Support...")
    mw = MainWindow()
    print("[GUI Debug] Main window created")
    
    # Default to login widget on startup
    mw.show_login()
    print("[GUI Debug] Set initial widget to login")
    
    # Show the window
    mw.show()
    print("[GUI Debug] Main window displayed")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()