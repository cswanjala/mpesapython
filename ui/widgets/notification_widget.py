import platform
import ctypes
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import QTimer, QPropertyAnimation, Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QScreen, QColor

# Optional Windows native toast notifier (for sound and system toast)
try:
    from winotify import Notification, audio
    _HAS_WINOTIFY = True
except Exception:
    _HAS_WINOTIFY = False


class MultiDesktopNotificationWindow(QWidget):
    """A notification that appears on ALL virtual desktops and ALL screens"""
    
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        
        # ULTRA-FORCEFUL window flags for multi-desktop support
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |          # Always on top
            Qt.WindowType.FramelessWindowHint |           # No title bar
            Qt.WindowType.Tool |                          # No taskbar entry
            Qt.WindowType.X11BypassWindowManagerHint |    # Bypass window manager (Linux)
            Qt.WindowType.WindowDoesNotAcceptFocus |      # Don't steal focus
            Qt.WindowType.MSWindowsFixedSizeDialogHint    # Better multi-desktop support on Windows
        )
        
        # Make it truly top-most and visible on all virtual desktops
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Create notification cards for ALL screens
        self.notification_cards = []
        self.create_notifications_for_all_screens(title, message)
        
        # Auto-close timer
        self.auto_close_timer = QTimer()
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(self.animate_out)
        self.auto_close_timer.start(15000)  # 15 seconds
        
        # Force to top immediately on all desktops
        QTimer.singleShot(100, self.force_to_all_desktops)
        
    def create_notifications_for_all_screens(self, title: str, message: str):
        """Create notification cards for EVERY screen and virtual desktop"""
        screens = QGuiApplication.screens()
        print(f"[MultiDesktop] Creating notifications for {len(screens)} screens")
        
        for screen in screens:
            # Create a notification card for each screen
            card = PaymentNotificationCard(title, message, self)
            card.dismissed.connect(self.on_card_dismissed)
            self.notification_cards.append(card)
            
            # Position card at center of this specific screen
            self.center_notification_on_screen(card, screen)
            
    def center_notification_on_screen(self, card, screen):
        """Position the notification card at bottom-right of the given screen (like a toast)"""
        geo = screen.geometry()
        margin = 32
        x = geo.x() + geo.width() - card.width() - margin
        y = geo.y() + geo.height() - card.height() - margin

        card.move(x, y)
        card.show()
        
    def showEvent(self, event):
        """Animate in when shown"""
        super().showEvent(event)
        self.force_to_all_desktops()
        for card in self.notification_cards:
            card.animate_in()
        
    def force_to_all_desktops(self):
        """Force the window to be visible on ALL virtual desktops using platform-specific methods"""
        try:
            if platform.system() == 'Windows':
                self._force_windows_all_desktops()
            elif platform.system() == 'Linux':
                self._force_linux_all_desktops()
            else:  # macOS and others
                self._force_generic_all_desktops()
                
            # Force all cards to be visible
            for card in self.notification_cards:
                card.raise_()
                card.activateWindow()
                card.show()
                
        except Exception as e:
            print(f"[MultiDesktop] Error forcing to all desktops: {e}")
            
    def _force_windows_all_desktops(self):
        """Windows-specific: Make window visible on all virtual desktops"""
        try:
            # Try to use Windows API to show on all virtual desktops
            HWND_TOPMOST = -1
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_SHOWWINDOW = 0x0040
            flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
            
            for card in self.notification_cards:
                hwnd = int(card.winId())
                # Set as topmost
                ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags)
                # Additional forceful methods
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                
                # Try to make it visible on all virtual desktops (Windows 10+)
                try:
                    # This is the key for virtual desktop support
                    GWL_EXSTYLE = -20
                    WS_EX_TOOLWINDOW = 0x00000080
                    WS_EX_NOACTIVATE = 0x08000000
                    
                    # Get current style
                    current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                    # Add toolwindow and noactivate flags for better multi-desktop behavior
                    new_style = current_style | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
                    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
                    
                except Exception as e:
                    print(f"[Windows Virtual Desktop] Fallback: {e}")
                    
        except Exception as e:
            print(f"[Windows All Desktops Error] {e}")
            
    def _force_linux_all_desktops(self):
        """Linux-specific: Make window visible on all workspaces"""
        try:
            for card in self.notification_cards:
                hwnd = int(card.winId())
                # Use xdotool to set on all workspaces
                import subprocess
                wid = hex(hwnd)
                # Try to set sticky flag (visible on all workspaces)
                subprocess.run(['xdotool', 'set_window', '--classname', 'MPesaNotification', wid], timeout=2)
                subprocess.run(['wmctrl', '-i', '-r', wid, '-b', 'add,sticky'], timeout=2)
        except:
            # Fallback - just ensure visibility
            for card in self.notification_cards:
                card.raise_()
                card.show()
            
    def _force_generic_all_desktops(self):
        """Generic method for other platforms"""
        for card in self.notification_cards:
            card.raise_()
            card.activateWindow()
            card.show()
            
    def on_card_dismissed(self):
        """When any card is dismissed, dismiss all"""
        self.animate_out()
        
    def animate_out(self):
        """Animate out and close all cards"""
        for card in self.notification_cards:
            card.animate_out()
        QTimer.singleShot(500, self.close_all)
        
    def close_all(self):
        """Close all notification cards"""
        for card in self.notification_cards:
            card.close()
        self.close()


class PaymentNotificationCard(QWidget):
    """A toast-style payment notification card (small, bottom-right, rounded, shadowed)"""
    dismissed = pyqtSignal()

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setFixedSize(340, 110)
        self.setStyleSheet("""
            QWidget {
                background: rgba(30, 41, 59, 0.96);
                border-radius: 16px;
                border: 1.5px solid #2563eb;
                color: #f1f5f9;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)
        
        # Header: icon and title
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("💰")
        icon_label.setStyleSheet("font-size: 22px; margin-right: 8px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #f1f5f9; margin: 0px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(22, 22)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #f1f5f9;
                border: none;
                border-radius: 11px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: white;
            }
        """)
        close_btn.clicked.connect(self.on_dismiss)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Message content
        message_label = QLabel(message)
        message_label.setStyleSheet("font-size: 13px; color: #e0e7ef; line-height: 1.5; margin-top: 2px;")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Timestamp
        timestamp = QLabel(datetime.now().strftime("%H:%M:%S"))
        timestamp.setStyleSheet("font-size: 11px; color: #a5b4fc; font-style: italic; margin-top: 2px;")
        layout.addWidget(timestamp)
        
        self.setLayout(layout)
        
        # Fade in effect
        self.setWindowOpacity(0.0)
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(350)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(31, 38, 135, 90))
        self.setGraphicsEffect(shadow)
        
        # Play sound if available
        self._play_notification_sound()
        
    def _play_notification_sound(self):
        """Play a notification sound on ALL platforms"""
        try:
            if platform.system() == 'Windows':
                import winsound
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
            elif platform.system() == 'Darwin':  # macOS
                import os
                os.system('afplay /System/Library/Sounds/Glass.aiff &')
            elif platform.system() == 'Linux':
                import os
                os.system('paplay /usr/share/sounds/freedesktop/stereo/message.oga &')
        except Exception as e:
            print(f"[Toast] Sound error: {e}")
            
    def setup_animation(self):
        pass  # No longer needed for toast style
    
    def animate_in(self):
        # Fade in (already handled in __init__)
        pass
    
    def animate_out(self):
        """Fade out and close"""
        fade = QPropertyAnimation(self, b"windowOpacity")
        fade.setDuration(300)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.finished.connect(self.close)
        fade.start()
        
    def on_dismiss(self):
        self.animate_out()
        QTimer.singleShot(400, self.dismissed.emit)