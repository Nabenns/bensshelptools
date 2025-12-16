import discord
import aiohttp
import os
import re
import uuid
from datetime import datetime

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1/signals")
TARGET_CHANNELS = [int(id) for id in os.getenv("TARGET_CHANNELS", "").split(",") if id]

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

def parse_signal(content: str):
    """
    Advanced parser for signals.
    Supports:
    - XAUUSD SELL LIMIT @ 2050
    - XAUUSD SELL AREA 4341- 4344
    - TP 1 50 PIPS
    - TP 2 100 PIPS
    - Emojis handling
    """
    # Clean content: Remove emojis (keep alphanumeric, spaces, punctuation)
    # This is a simple way to avoid emoji interference, though regex usually ignores them if not matched.
    # content = re.sub(r'[^\w\s\d\.\-\:\@]', '', content) 
    
    content = content.upper()
    
    # 1. Extract Symbol
    symbol_match = re.search(r"(XAUUSD|EURUSD|GBPUSD|BTCUSD|US30|NAS100)", content)
    if not symbol_match:
        return None
    symbol = symbol_match.group(1)

    # 2. Extract Type
    type_str = "MARKET_EXECUTION"
    if "BUY" in content:
        type_str = "BUY"
    elif "SELL" in content:
        type_str = "SELL"
    
    if "LIMIT" in content or "AREA" in content:
        type_str += "_LIMIT"
    elif "STOP" in content:
        type_str += "_STOP"

    # 3. Extract Entry Price
    # Matches: @ 2050, AREA 4341- 4344
    entry_price = 0.0
    # Range match: AREA 4341- 4344
    range_match = re.search(r"AREA\s*(\d+(\.\d+)?)\s*-\s*(\d+(\.\d+)?)", content)
    if range_match:
        entry_price = float(range_match.group(1)) # Take start of range
    else:
        price_match = re.search(r"(@|AT)\s*(\d+(\.\d+)?)", content)
        if price_match:
            entry_price = float(price_match.group(2))

    # 4. Extract SL
    sl = 0.0
    # Matches: SL 4347, SL: 4347
    sl_match = re.search(r"SL\s*:?\s*(\d+(\.\d+)?)", content)
    if sl_match:
        sl = float(sl_match.group(1))

    # 5. Extract TP 1 & TP 2
    tp1 = 0.0
    tp2 = 0.0
    
    # Pip Value Logic
    pip_value = 0.0001
    if "XAU" in symbol or "JPY" in symbol:
        pip_value = 0.1 # Standard for Gold/JPY (0.1 / 0.01 depending on digits, using 0.1 safe baseline for Gold)

    def calculate_tp(price_or_pips, is_pips):
        if not is_pips:
            return float(price_or_pips)
        
        pips = float(price_or_pips)
        if "BUY" in type_str:
            return entry_price + (pips * pip_value)
        else:
            return entry_price - (pips * pip_value)

    # TP 1
    # Matches: TP 1 50 PIPS, TP1 50 PIPS, TP 1 2050
    tp1_match = re.search(r"TP\s*1\s*:?\s*(\d+(\.\d+)?)\s*(PIPS)?", content)
    if tp1_match:
        val = tp1_match.group(1)
        is_pips = bool(tp1_match.group(3)) or "PIPS" in content[tp1_match.end():tp1_match.end()+10] # Check lookahead roughly
        tp1 = calculate_tp(val, is_pips)

    # TP 2
    tp2_match = re.search(r"TP\s*2\s*:?\s*(\d+(\.\d+)?)\s*(PIPS)?", content)
    if tp2_match:
        val = tp2_match.group(1)
        is_pips = bool(tp2_match.group(3)) or "PIPS" in content[tp2_match.end():tp2_match.end()+10]
        tp2 = calculate_tp(val, is_pips)
        
    # Fallback: Single TP found without number
    if tp1 == 0.0:
        tp_match = re.search(r"TP\s*:?\s*(\d+(\.\d+)?)\s*(PIPS)?", content)
        if tp_match:
            val = tp_match.group(1)
            is_pips = bool(tp_match.group(3))
            tp1 = calculate_tp(val, is_pips)

    # Rounding
    if pip_value == 0.1:
        tp1 = round(tp1, 2)
        tp2 = round(tp2, 2)
    else:
        tp1 = round(tp1, 5)
        tp2 = round(tp2, 5)

    if symbol and entry_price > 0 and sl > 0 and tp1 > 0:
        return {
            "id": str(uuid.uuid4()),
            "symbol": symbol,
            "type": type_str,
            "entry_price": entry_price,
            "stop_loss": sl,
            "take_profit": tp1,      # Primary TP
            "take_profit_2": tp2,    # Secondary TP (0.0 if not found)
            "timestamp": datetime.now().isoformat(),
            "source": "discord"
        }
    return None

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Check if channel is monitored (if TARGET_CHANNELS is set)
    if TARGET_CHANNELS and message.channel.id not in TARGET_CHANNELS:
        return

    print(f"Received message: {message.content}")
    
    signal_data = parse_signal(message.content)
    
    if signal_data:
        print(f"Parsed Signal: {signal_data}")
        # Send to Backend
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(BACKEND_URL, json=signal_data) as response:
                    if response.status == 200:
                        print("Signal sent to backend successfully")
                        await message.add_reaction("✅")
                    else:
                        print(f"Failed to send signal: {response.status}")
                        await message.add_reaction("❌")
            except Exception as e:
                print(f"Error sending to backend: {e}")
                await message.add_reaction("⚠️")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not found in environment variables.")
    else:
        client.run(DISCORD_TOKEN)
