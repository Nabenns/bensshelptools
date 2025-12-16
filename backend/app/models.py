from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime

class SignalType(str, Enum):
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"
    MARKET_EXECUTION = "MARKET_EXECUTION" # Fallback

class Signal(BaseModel):
    id: str
    symbol: str
    type: SignalType
    entry_price: float
    stop_loss: float
    take_profit: float
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    timestamp: datetime = datetime.now()
    source: str = "discord"

class SignalCreate(BaseModel):
    raw_message: str
    channel_id: str
