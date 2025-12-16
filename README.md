# CopySignal: Discord to MT5 Automation

## Overview
This project automates trading signals from Discord to MetaTrader 5 (MT5) without using the MT5 API directly. It uses a desktop client to bridge signals to an Expert Advisor (EA) running in MT5.

## Components
1.  **Backend**: FastAPI + Redis + Discord Bot (Dockerized).
2.  **Desktop Client**: PySide6 application for the user.
3.  **MT5 EA**: MQL5 script to execute trades.

## Setup Instructions

### 1. Backend (Server)
You need Docker installed.
1.  Create a `.env` file in `backend/` with:
    ```
    DISCORD_TOKEN=your_discord_bot_token
    TARGET_CHANNELS=123456789,987654321
    ```
2.  Run:
    ```bash
    docker-compose up --build
    ```

### 2. MT5 Expert Advisor
1.  Open MetaTrader 5.
2.  Open MetaEditor (F4).
3.  Copy `ea/CopySignal.mq5` to your MQL5 Experts folder.
4.  Compile it (F7).
5.  Attach the EA to any chart in MT5.
6.  **Important**: Enable "Allow DLL imports" and "Allow WebRequest" (if needed in future, though currently file-based).

### 3. Desktop Client
1.  Install dependencies:
    ```bash
    pip install -r client/requirements.txt
    ```
2.  Run the client:
    ```bash
    python client/app/main.py
    ```
3.  In the Client Settings tab, set the **MT5 Data Path** to:
    `%APPDATA%\MetaQuotes\Terminal\{InstanceID}\MQL5\Files\Signals`
    *Note: You may need to create the `Signals` folder manually inside `MQL5\Files`.*

## Usage
1.  Start the Backend.
2.  Start the Desktop Client.
3.  Start MT5 and attach the EA.
4.  Post a signal in your Discord channel:
    ```
    XAUUSD SELL LIMIT @ 2050
    SL: 2060
    TP: 2040
    ```
5.  Watch it execute in MT5!
