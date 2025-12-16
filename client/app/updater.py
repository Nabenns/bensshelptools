import requests
import sys
import os
import subprocess
import logging
from packaging import version
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QThread, Signal

# URL where the version.json file is hosted
# We use the raw GitHub URL of the WEB repo because that's where we committed version.json
VERSION_URL = "https://raw.githubusercontent.com/Nabenns/webnyabensshelptools/main/public/version.json"

CURRENT_VERSION = "1.0.0"

class UpdateChecker(QThread):
    update_available = Signal(str, str) # version, download_url
    no_update = Signal()
    error_occurred = Signal(str)

    def run(self):
        try:
            response = requests.get(VERSION_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            latest_version = data.get("latest_version")
            download_url = data.get("download_url")

            if not latest_version or not download_url:
                self.error_occurred.emit("Invalid version info from server.")
                return

            if version.parse(latest_version) > version.parse(CURRENT_VERSION):
                self.update_available.emit(latest_version, download_url)
            else:
                self.no_update.emit()

        except Exception as e:
            self.error_occurred.emit(str(e))

class Updater:
    def __init__(self, parent=None):
        self.parent = parent
        self.checker = UpdateChecker()
        self.checker.update_available.connect(self.on_update_available)
        self.checker.error_occurred.connect(self.on_error)
        
    def check_for_updates(self, silent=True):
        self.silent = silent
        self.checker.start()

    def on_update_available(self, new_version, download_url):
        reply = QMessageBox.question(
            self.parent, 
            "Update Available", 
            f"A new version ({new_version}) is available.\nDo you want to download and install it now?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.download_and_install(download_url)

    def on_error(self, error_msg):
        if not self.silent:
            QMessageBox.warning(self.parent, "Update Check Failed", f"Could not check for updates:\n{error_msg}")

    def download_and_install(self, url):
        # 1. Download the installer
        try:
            import tempfile
            installer_path = os.path.join(tempfile.gettempdir(), "BenssHelpTools_Setup.exe")
            
            # Show progress dialog (simplified for now, blocking download)
            # In a real app, use a thread and progress bar
            QMessageBox.information(self.parent, "Downloading", "Downloading update... The app will close shortly.")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(installer_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 2. Run the installer
            # Use /SILENT or /VERYSILENT to install without user interaction if desired
            # But usually for a major update, standard UI is fine.
            subprocess.Popen([installer_path])
            
            # 3. Close current app
            sys.exit(0)
            
        except Exception as e:
            QMessageBox.critical(self.parent, "Update Failed", f"Failed to download update:\n{e}")
