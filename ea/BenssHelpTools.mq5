//+------------------------------------------------------------------+
//|                                              BenssHelpTools.mq5 |
//|                                  Copyright 2024, BenssHelpTools |
//|                                             https://copysignal.io |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, BenssHelpTools"
#property link      "https://copysignal.io"
#property version   "1.00"

#include <Trade\Trade.mqh>
#include <Files\FileTxt.mqh>

CTrade trade;

input string SignalPath = "Signals"; // Subfolder in MQL5/Files

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   Print("BenssHelpTools EA Started. Monitoring path: ", SignalPath);
   EventSetTimer(1); // Check for signals every 1 second
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   EventKillTimer();
  }

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   ManageTrades(); // Check for Auto BEP / Trailing
  }

//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
  {
   ScanForSignals();
  }

//+------------------------------------------------------------------+
//| Scan for new signal files                                        |
//+------------------------------------------------------------------+
void ScanForSignals()
  {
   string file_name;
   long search_handle=FileFindFirst(SignalPath+"\\*.json", file_name);
   
   if(search_handle!=INVALID_HANDLE)
     {
      do
        {
         Print("Found signal file: ", file_name);
         ProcessSignalFile(file_name);
         
         // Delete file after processing
         FileDelete(SignalPath+"\\"+file_name);
         
        }
      while(FileFindNext(search_handle, file_name));
      FileFindClose(search_handle);
     }
  }

//+------------------------------------------------------------------+
//| Process a single signal file                                     |
//+------------------------------------------------------------------+
void ProcessSignalFile(string file_name)
  {
   int file_handle = FileOpen(SignalPath+"\\"+file_name, FILE_READ|FILE_TXT|FILE_ANSI);
   if(file_handle != INVALID_HANDLE)
     {
      string json_content = "";
      while(!FileIsEnding(file_handle))
        {
         json_content += FileReadString(file_handle);
        }
      FileClose(file_handle);
      
      Print("Content: ", json_content);
      
      // Simple JSON parsing (MQL5 doesn't have native JSON, doing manual parsing for MVP)
      // Assuming format: {"symbol": "XAUUSD", "type": "SELL_LIMIT", "entry_price": 2050.0, ...}
      
      string symbol = ExtractJsonValue(json_content, "symbol");
      string type = ExtractJsonValue(json_content, "type");
      double price = StringToDouble(ExtractJsonValue(json_content, "entry_price"));
      double sl = StringToDouble(ExtractJsonValue(json_content, "stop_loss"));
      double tp = StringToDouble(ExtractJsonValue(json_content, "take_profit"));
      double tp2 = StringToDouble(ExtractJsonValue(json_content, "take_profit_2"));
      
      string risk_type = ExtractJsonValue(json_content, "risk_type");
      double risk_value = StringToDouble(ExtractJsonValue(json_content, "risk_value"));
      
      double total_volume = CalculateLotSize(symbol, price, sl, risk_type, risk_value);
      
      if(tp2 > 0)
        {
         // Split volume for 2 positions
         double vol1 = NormalizeDouble(total_volume / 2.0, 2);
         double vol2 = total_volume - vol1; // Remainder to ensure total matches
         
         // Ensure min lot
         double min_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
         if(vol1 < min_lot) vol1 = min_lot;
         if(vol2 < min_lot) vol2 = min_lot;
         
         ExecuteTrade(symbol, type, vol1, price, sl, tp);
         ExecuteTrade(symbol, type, vol2, price, sl, tp2);
        }
      else
        {
         ExecuteTrade(symbol, type, total_volume, price, sl, tp);
        }
     }
  }

//+------------------------------------------------------------------+
//| Calculate Lot Size based on Risk                                 |
//+------------------------------------------------------------------+
double CalculateLotSize(string symbol, double entry_price, double sl_price, string risk_type, double risk_value)
  {
   if(risk_type == "FIXED" || risk_value <= 0)
     {
      return risk_value > 0 ? risk_value : 0.01;
     }
     
   // Calculate for Risk %
   if(sl_price <= 0) return 0.01; // Cannot calculate without SL
   
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amount = balance * (risk_value / 100.0);
   
   double tick_size = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
   double tick_value = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
   
   if(tick_size == 0 || tick_value == 0) return 0.01;
   
   double points_risk = MathAbs(entry_price - sl_price);
   double loss_per_lot = (points_risk / tick_size) * tick_value;
   
   if(loss_per_lot == 0) return 0.01;
   
   double lot_size = risk_amount / loss_per_lot;
   
   // Normalize Lot Size
   double min_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double max_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double step_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   
   lot_size = MathFloor(lot_size / step_lot) * step_lot;
   
   if(lot_size < min_lot) lot_size = min_lot;
   if(lot_size > max_lot) lot_size = max_lot;
   
   Print("Calculated Risk Lot: ", lot_size, " (Risk: $", risk_amount, ")");
   return lot_size;
  }

//+------------------------------------------------------------------+
//| Helper to extract value from JSON string (Very Basic)            |
//+------------------------------------------------------------------+
string ExtractJsonValue(string json, string key)
  {
   int key_pos = StringFind(json, "\""+key+"\"");
   if(key_pos == -1) return "";
   
   int val_start = StringFind(json, ":", key_pos) + 1;
   int val_end = StringFind(json, ",", val_start);
   if(val_end == -1) val_end = StringFind(json, "}", val_start);
   
   string val = StringSubstr(json, val_start, val_end - val_start);
   
   // Clean up quotes and spaces
   StringReplace(val, "\"", "");
   StringTrimLeft(val);
   StringTrimRight(val);
   
   return val;
  }

//+------------------------------------------------------------------+
//| Execute the trade                                                |
//+------------------------------------------------------------------+
void ExecuteTrade(string symbol, string type, double volume, double price, double sl, double tp)
  {
   Print("Attempting Trade: ", symbol, " ", type, " Vol: ", volume, " @ ", price, " SL: ", sl, " TP: ", tp);
   
   // double volume = 0.01; // Removed fixed lot, using passed volume
   bool result = false;
   
   trade.SetExpertMagicNumber(123456);
   
   if(type == "BUY_LIMIT")
     {
      result = trade.BuyLimit(volume, price, symbol, sl, tp);
     }
   else if(type == "SELL_LIMIT")
     {
      result = trade.SellLimit(volume, price, symbol, sl, tp);
     }
   else if(type == "BUY_STOP")
     {
      result = trade.BuyStop(volume, price, symbol, sl, tp);
     }
   else if(type == "SELL_STOP")
     {
      result = trade.SellStop(volume, price, symbol, sl, tp);
     }
   else if(type == "MARKET_EXECUTION" || type == "BUY" || type == "SELL") 
     {
      // Simple market execution
      if(StringFind(type, "BUY") >= 0)
         result = trade.Buy(volume, symbol, 0, sl, tp);
      else
         result = trade.Sell(volume, symbol, 0, sl, tp);
     }
   else 
     {
      Print("Unknown signal type: ", type);
      return;
     }
     
   if(result)
     {
      Print("Trade Request Sent Successfully");
     }
   else
     {
      Print("Trade Failed. Error: ", GetLastError());
      // Reset error
      ResetLastError();
     }
  }

//+------------------------------------------------------------------+
//| Manage Open Trades (Auto BEP & Trailing)                         |
//+------------------------------------------------------------------+
void ManageTrades()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket <= 0) continue;
      
      if(PositionGetInteger(POSITION_MAGIC) != 123456) continue; // Only manage our trades
      
      string symbol = PositionGetString(POSITION_SYMBOL);
      double sl = PositionGetDouble(POSITION_SL);
      double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      double current_price = PositionGetDouble(POSITION_PRICE_CURRENT);
      long type = PositionGetInteger(POSITION_TYPE);
      
      double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
      
      // --- CONFIGURABLE SETTINGS (Hardcoded for now) ---
      int bep_trigger_pips = 20; // Move to BEP after 20 pips profit
      int bep_offset_pips = 2;   // Lock in 2 pips profit
      // ----------------------------------------------------------------
      
      double bep_trigger = bep_trigger_pips * point * 10; // Convert pips to points (assuming 5 digit broker)
      if(StringFind(symbol, "JPY") >= 0 || StringFind(symbol, "XAU") >= 0) bep_trigger = bep_trigger_pips * point * 100; // Adjust for JPY/Gold

      // BUY Logic
      if(type == POSITION_TYPE_BUY)
        {
         if(current_price >= open_price + bep_trigger)
           {
            double new_sl = open_price + (bep_offset_pips * point * 10);
            if(sl < new_sl || sl == 0) // Only move SL up
              {
               if(trade.PositionModify(ticket, new_sl, PositionGetDouble(POSITION_TP)))
                 {
                  Print("Auto BEP Triggered for Buy Ticket: ", ticket);
                 }
              }
           }
        }
      // SELL Logic
      else if(type == POSITION_TYPE_SELL)
        {
         if(current_price <= open_price - bep_trigger)
           {
            double new_sl = open_price - (bep_offset_pips * point * 10);
            if(sl > new_sl || sl == 0) // Only move SL down
              {
               if(trade.PositionModify(ticket, new_sl, PositionGetDouble(POSITION_TP)))
                 {
                  Print("Auto BEP Triggered for Sell Ticket: ", ticket);
                 }
              }
           }
        }
     }
  }
