import sys
import json
import asyncio
import threading
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot
import websockets
from ui import MainWindow

# Signal Handler Worker
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
                        
                        # TODO: Write to MT5 Bridge
                        
            except Exception as e:
                self.status_changed.emit("Disconnected")
                self.log_message.emit(f"Connection Error: {e}")
                await asyncio.sleep(5) # Retry delay

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    # Worker Thread for WebSocket
    # ws_url = "ws://localhost:8000/ws/signals" # Localhost
    ws_url = "wss://api.thetrader.id/ws/signals" # VPS Ngrok
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
