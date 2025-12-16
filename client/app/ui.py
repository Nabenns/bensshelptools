from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QLineEdit, QStatusBar, QTabWidget, QFrame)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BenssHelpTools Client")
        self.setMinimumSize(900, 650)
        
        # Apply Modern Dark Theme
        self.apply_stylesheet()

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("BenssHelpTools")
        title_label.setObjectName("TitleLabel")
        
        version_label = QLabel("v1.0")
        version_label.setObjectName("VersionLabel")
        
        self.status_label = QLabel("Disconnected")
        self.status_label.setObjectName("StatusBadgeDisconnected")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(version_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        layout.addLayout(header_layout)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Signal Monitor Tab
        self.signal_table = QTableWidget()
        self.signal_table.setColumnCount(7)
        self.signal_table.setHorizontalHeaderLabels(["Time", "Symbol", "Type", "Price", "SL", "TP1", "TP2"])
        self.signal_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.signal_table.verticalHeader().setVisible(False)
        self.signal_table.setAlternatingRowColors(True)
        self.signal_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.signal_table.setEditTriggers(QTableWidget.NoEditTriggers)
        tabs.addTab(self.signal_table, "Live Signals")

        # Settings Tab
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(15)
        
        # MT5 Path
        mt5_group = QWidget()
        mt5_layout = QVBoxLayout(mt5_group)
        mt5_layout.setContentsMargins(0, 0, 0, 0)
        mt5_layout.addWidget(QLabel("MT5 Data Path:"))
        self.mt5_path_input = QLineEdit()
        self.mt5_path_input.setPlaceholderText("C:\\Users\\...\\AppData\\Roaming\\MetaQuotes\\Terminal\\...\\MQL5\\Files")
        self.mt5_path_input.textChanged.connect(self.save_settings)
        mt5_layout.addWidget(self.mt5_path_input)
        settings_layout.addWidget(mt5_group)

        # Risk Settings
        risk_group = QWidget()
        risk_layout = QHBoxLayout(risk_group)
        risk_layout.setContentsMargins(0, 10, 0, 10)
        
        risk_layout.addWidget(QLabel("Risk Type:"))
        from PySide6.QtWidgets import QComboBox
        self.risk_type_combo = QComboBox()
        self.risk_type_combo.addItems(["Fixed Lot", "Risk % per Trade"])
        self.risk_type_combo.currentTextChanged.connect(self.save_settings)
        risk_layout.addWidget(self.risk_type_combo)
        
        risk_layout.addWidget(QLabel("Value:"))
        self.risk_value_input = QLineEdit()
        self.risk_value_input.setPlaceholderText("0.01 or 1.0")
        self.risk_value_input.textChanged.connect(self.save_settings)
        risk_layout.addWidget(self.risk_value_input)
        
        settings_layout.addWidget(risk_group)
        
        settings_layout.addStretch()
        tabs.addTab(settings_widget, "Settings")

        # Logs
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.addWidget(QLabel("Activity Logs"))
        
        self.log_widget = QTableWidget()
        self.log_widget.setColumnCount(2)
        self.log_widget.setHorizontalHeaderLabels(["Time", "Message"])
        self.log_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.log_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.log_widget.verticalHeader().setVisible(False)
        self.log_widget.setAlternatingRowColors(True)
        self.log_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        
        log_layout.addWidget(self.log_widget)
        layout.addWidget(log_container)
        
        # Load Settings
        self.load_settings()

    def apply_stylesheet(self):
        style = """
        QMainWindow {
            background-color: #121212; /* Darker, more solid background */
        }
        QWidget {
            color: #e0e0e0;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
        }
        
        /* Header Styling */
        QLabel#TitleLabel {
            font-size: 26px;
            font-weight: 800;
            color: #ffffff;
            padding-left: 5px;
        }
        QLabel#VersionLabel {
            font-size: 12px;
            color: #888888;
            margin-bottom: 5px;
            margin-left: 5px;
            font-weight: bold;
        }
        
        /* Status Badges */
        QLabel#StatusBadgeConnected {
            background-color: #059669; /* Darker Green */
            color: white;
            padding: 6px 12px;
            border-radius: 14px;
            font-weight: bold;
            font-size: 12px;
            border: 1px solid #10b981;
        }
        QLabel#StatusBadgeDisconnected {
            background-color: #b91c1c; /* Darker Red */
            color: white;
            padding: 6px 12px;
            border-radius: 14px;
            font-weight: bold;
            font-size: 12px;
            border: 1px solid #ef4444;
        }
        
        /* Tabs */
        QTabWidget::pane {
            border: 1px solid #333333;
            background: #1e1e1e;
            border-radius: 8px;
            top: -1px; 
        }
        QTabBar::tab {
            background: #2d2d2d;
            color: #888888;
            padding: 10px 25px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            margin-right: 4px;
            font-weight: 600;
        }
        QTabBar::tab:selected {
            background: #1e1e1e;
            color: #ffffff;
            border-bottom: 2px solid #3b82f6; /* Blue accent */
        }
        QTabBar::tab:hover {
            background: #333333;
            color: #ffffff;
        }
        
        /* Tables */
        QTableWidget {
            background-color: #1e1e1e;
            alternate-background-color: #252526; /* Explicit dark alternate color */
            border: none;
            gridline-color: transparent; /* Cleaner look without gridlines */
            selection-background-color: #2d2d2d;
            selection-color: white;
            outline: none;
        }
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #333333; /* Subtle separator */
        }
        QTableWidget::item:selected {
            background-color: #374151;
            border-left: 3px solid #3b82f6; /* Accent indicator */
        }
        QHeaderView::section {
            background-color: #121212;
            color: #9ca3af;
            padding: 8px;
            border: none;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 12px;
            border-bottom: 2px solid #333333;
        }
        
        /* Inputs */
        QLineEdit {
            background-color: #2d2d2d;
            border: 1px solid #404040;
            border-radius: 6px;
            padding: 10px;
            color: white;
            font-size: 14px;
        }
        QLineEdit:focus {
            border: 1px solid #3b82f6;
            background-color: #333333;
        }
        
        /* ComboBox */
        QComboBox {
            background-color: #2d2d2d;
            border: 1px solid #404040;
            border-radius: 6px;
            padding: 10px;
            color: white;
            min-width: 150px;
        }
        QComboBox:hover {
            background-color: #333333;
        }
        QComboBox::drop-down {
            border: none;
            width: 30px;
        }
        QComboBox QAbstractItemView {
            background-color: #2d2d2d;
            color: white;
            selection-background-color: #3b82f6;
            border: 1px solid #404040;
        }
        
        /* Scrollbars */
        QScrollBar:vertical {
            border: none;
            background: #121212;
            width: 8px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #4b5563;
            min-height: 20px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical:hover {
            background: #6b7280;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """
        self.setStyleSheet(style)

    def load_settings(self):
        import json
        import os
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    self.mt5_path_input.setText(settings.get("mt5_path", ""))
                    self.risk_type_combo.setCurrentText(settings.get("risk_type", "Fixed Lot"))
                    self.risk_value_input.setText(str(settings.get("risk_value", "0.01")))
            except:
                pass

    def save_settings(self):
        import json
        settings = {
            "mt5_path": self.mt5_path_input.text(),
            "risk_type": self.risk_type_combo.currentText(),
            "risk_value": self.risk_value_input.text()
        }
        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f)
        except:
            pass

    @Slot(dict)
    def process_signal(self, signal_data):
        # 1. Update UI
        self.add_signal(signal_data)
        
        # 2. Inject Risk Settings
        signal_data["risk_type"] = "PERCENT" if self.risk_type_combo.currentText() == "Risk % per Trade" else "FIXED"
        try:
            signal_data["risk_value"] = float(self.risk_value_input.text())
        except:
            signal_data["risk_value"] = 0.01 # Default fallback
        
        # 2. Write to MT5
        mt5_path = self.mt5_path_input.text()
        if mt5_path:
            from bridge import MT5Bridge
            bridge = MT5Bridge(mt5_path)
            success = bridge.write_signal(signal_data)
            if success:
                self.log_message(f"Signal sent to MT5: {signal_data['symbol']}")
            else:
                self.log_message("Failed to write to MT5 path")
        else:
            self.log_message("MT5 Path not set! Signal not sent.")

    @Slot(dict)
    def add_signal(self, signal_data):
        row = self.signal_table.rowCount()
        self.signal_table.insertRow(row)
        
        # Helper to create item
        def create_item(text, color=None):
            item = QTableWidgetItem(str(text))
            item.setTextAlignment(Qt.AlignCenter)
            if color:
                item.setForeground(QColor(color))
            return item

        self.signal_table.setItem(row, 0, create_item(signal_data.get("timestamp", "").split("T")[1][:8])) # Show time only
        self.signal_table.setItem(row, 1, create_item(signal_data.get("symbol", ""), "#ffffff"))
        
        # Color code Type
        sig_type = signal_data.get("type", "")
        type_color = "#4ade80" if "BUY" in sig_type else "#f87171" if "SELL" in sig_type else "#ffffff"
        self.signal_table.setItem(row, 2, create_item(sig_type, type_color))
        
        self.signal_table.setItem(row, 3, create_item(signal_data.get("entry_price", "")))
        self.signal_table.setItem(row, 4, create_item(signal_data.get("stop_loss", ""), "#f87171"))
        self.signal_table.setItem(row, 5, create_item(signal_data.get("take_profit", ""), "#4ade80"))
        
        tp2 = signal_data.get("take_profit_2", 0.0)
        tp2_text = str(tp2) if tp2 > 0 else "-"
        self.signal_table.setItem(row, 6, create_item(tp2_text, "#4ade80"))

    @Slot(str)
    def update_status(self, status):
        self.status_label.setText(status)
        if status == "Connected":
            self.status_label.setObjectName("StatusBadgeConnected")
        else:
            self.status_label.setObjectName("StatusBadgeDisconnected")
        # Force style reload for the label
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    @Slot(str)
    def log_message(self, message):
        row = self.log_widget.rowCount()
        self.log_widget.insertRow(row)
        from datetime import datetime
        time_item = QTableWidgetItem(datetime.now().strftime("%H:%M:%S"))
        msg_item = QTableWidgetItem(message)
        self.log_widget.setItem(row, 0, time_item)
        self.log_widget.setItem(row, 1, msg_item)
