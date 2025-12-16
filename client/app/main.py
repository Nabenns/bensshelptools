import sys
import json
import asyncio
import threading
import subprocess
import requests
import os
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import QObject, Signal, Slot, Qt
import websockets
from ui import MainWindow
from updater import Updater

# --- License Logic ---
def get_hwid():
    try:
        # Windows only
        cmd = 'wmic csproduct get uuid'
        uuid = str(subprocess.check_output(cmd).decode().split('\n')[1].strip())
        return uuid
    except:
        return "UNKNOWN_HWID"

class LicenseDialog(QDialog):
    def __init__(self, settings_path):
        super().__init__()
        self.setWindowTitle("Activate License")
        self.setFixedSize(450, 280)
        self.settings_path = settings_path
        
        # Modern Dark Theme Styling
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1b26;
                color: #ffffff;
            }
            QLabel {
                color: #a9b1d6;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #24283b;
                border: 1px solid #414868;
                border-radius: 8px;
                color: #c0caf5;
                padding: 12px;
                font-size: 14px;
                font-family: 'Consolas', monospace;
            }
            QLineEdit:focus {
                border: 1px solid #7aa2f7;
                background-color: #292e42;
            }
            QPushButton {
                background-color: #7aa2f7;
                color: #1a1b26;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #bb9af7;
            }
            QPushButton:pressed {
                background-color: #3d59a1;
            }
            QPushButton:disabled {
                background-color: #414868;
                color: #565f89;
            }
        """)

        self.layout = QVBoxLayout()
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(40, 40, 40, 40)
        
        # Header
        title = QLabel("BenssHelpTools")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #7aa2f7; margin-bottom: 5px;")
        subtitle = QLabel("Please enter your license key to continue.")
        subtitle.setStyleSheet("font-size: 13px; color: #565f89; margin-bottom: 10px;")
        
        self.layout.addWidget(title)
        self.layout.addWidget(subtitle)
        
        # Input
        self.input = QLineEdit()
        self.input.setPlaceholderText("TRADER-XXXX-XXXX")
        self.layout.addWidget(self.input)
        
        # Button
        self.btn = QPushButton("Activate License")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.clicked.connect(self.validate)
        self.layout.addWidget(self.btn)
        
        self.setLayout(self.layout)
        
        # Load saved key
        self.settings = self.load_settings()
        if "license_key" in self.settings:
            self.input.setText(self.settings["license_key"])

    def load_settings(self):
        try:
            with open(self.settings_path, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_key(self, key):
        self.settings["license_key"] = key
        with open(self.settings_path, 'w') as f:
            json.dump(self.settings, f)

    def validate(self):
        key = self.input.text().strip()
        if not key:
            QMessageBox.warning(self, "Error", "Please enter a license key")
            return
            
        self.btn.setEnabled(False)
        self.btn.setText("Checking...")
        
        hwid = get_hwid()
        # Use local URL for dev, update to production URL for release
        # API_URL = "http://127.0.0.1:8000/dashboard/validate" 
        API_URL = "https://api.thetrader.id/dashboard/validate"

        try:
            response = requests.post(API_URL, json={"key": key, "hwid": hwid}, timeout=10)
            
            try:
                data = response.json()
            except:
                # Handle non-JSON response (e.g. 502 Bad Gateway, 404 HTML page)
                QMessageBox.critical(self, "Server Error", f"Server returned unexpected response ({response.status_code}).\n\n{response.text[:100]}...")
                self.btn.setEnabled(True)
                self.btn.setText("Activate License")
                return
            
            if response.status_code == 200 and data.get("valid"):
                self.save_key(key)
                QMessageBox.information(self, "Success", f"License Active!\nExpires: {data.get('expires_at')}")
                self.accept()
            else:
                # Support both 'message' (our API) and 'detail' (FastAPI default error)
                error_msg = data.get("message") or data.get("detail") or "Unknown validation error"
                QMessageBox.critical(self, "Activation Failed", f"{error_msg}")
                self.btn.setEnabled(True)
                self.btn.setText("Activate License")

        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Connection Error", "Could not connect to the server.\nPlease check your internet connection or URL.")
            self.btn.setEnabled(True)
            self.btn.setText("Activate License")
        except Exception as e:
            QMessageBox.critical(self, "System Error", f"An unexpected error occurred:\n{str(e)}")
            self.btn.setEnabled(True)
            self.btn.setText("Activate License")

# --- Signal Worker ---
class SignalWorker(QObject):
    signal_received = Signal(dict)
    status_changed = Signal(str)
    log_message = Signal(str)

    def __init__(self, ws_url):
        super().__init__()
        self.ws_url = ws_url
        self.running = True

    def run(self):
        asyncio.run(self.connect_ws())

    async def connect_ws(self):
        while self.running:
            try:
                self.status_changed.emit("Connecting...")
                async with websockets.connect(self.ws_url) as websocket:
                    self.status_changed.emit("Connected")
                    self.log_message.emit("Connected to Signal Server")
                    
                    while self.running:
                        message = await websocket.recv()
                        data = json.loads(message)
                        self.signal_received.emit(data)
                        self.log_message.emit(f"Signal Received: {data['symbol']} {data['type']}")
                        
            except Exception as e:
                self.status_changed.emit("Disconnected")
                self.log_message.emit(f"Connection Error: {e}")
                await asyncio.sleep(5) # Retry delay

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 1. License Check
    settings_path = "settings.json"
    license_dialog = LicenseDialog(settings_path)
    
    # Show dialog if not activated or just to be safe
    if license_dialog.exec() != QDialog.Accepted:
        sys.exit()

    # 2. Main App
    window = MainWindow()
    window.show()

    # 3. Auto-Updater Check
    updater = Updater(window)
    updater.check_for_updates(silent=True)

    # 4. Worker Thread for WebSocket
    # ws_url = "ws://localhost:8000/ws/signals" # Localhost
    ws_url = "wss://api.thetrader.id/ws/signals" # VPS Production
    worker = SignalWorker(ws_url)
    
    # Connect signals
    worker.signal_received.connect(window.process_signal)
    worker.status_changed.connect(window.update_status)
    worker.log_message.connect(window.log_message)

    thread = threading.Thread(target=worker.run, daemon=True)
    thread.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
