import os
import json
import logging

class MT5Bridge:
    def __init__(self, mt5_files_path: str):
        self.mt5_files_path = mt5_files_path
        self.logger = logging.getLogger(__name__)

    def write_signal(self, signal_data: dict):
        """
        Writes the signal to a JSON file in the MT5 Common/Files or MQL5/Files directory.
        """
        if not os.path.exists(self.mt5_files_path):
            self.logger.error(f"MT5 Path does not exist: {self.mt5_files_path}")
            return False

        # Ensure Signals subdirectory exists to match EA default
        signals_dir = os.path.join(self.mt5_files_path, "Signals")
        if not os.path.exists(signals_dir):
            try:
                os.makedirs(signals_dir)
            except Exception as e:
                self.logger.error(f"Failed to create Signals dir: {e}")
                return False

        # Filename: signal_{id}.json
        filename = f"signal_{signal_data['id']}.json"
        filepath = os.path.join(signals_dir, filename)

        try:
            with open(filepath, 'w') as f:
                json.dump(signal_data, f)
            self.logger.info(f"Signal written to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to write signal: {e}")
            return False
