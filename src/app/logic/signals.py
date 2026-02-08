import pandas as pd
from typing import Dict, Any

def generate_trade_plan(df: pd.DataFrame, score_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Entry, SL, TP based on analysis.
    """
    if df.empty or len(df) < 20:
        return {}
        
    row = df.iloc[-1]
    
    # Logic:
    # Entry: Current Close to High (or breakout level)
    # SL: Recent Swing Low or EMA50 (if close) or EMA20 (aggressive)
    # TP: 1.5R, 2R
    
    # 1. SL
    # Aggressive: EMA20
    # Conservative: EMA50 - buffer
    
    sl_level = row['ema20'] # Default to EMA20 support
    if row['close'] < row['ema20']: 
        # Below EMA20, use Swing Low
        sl_level = df['low'].rolling(20).min().iloc[-1]
    
    atr = row['atr']
    sl_level = sl_level - (0.5 * atr) # Buffer
    
    # Avoid SL > Close
    if sl_level >= row['close']:
        sl_level = row['close'] * 0.95 # Fallback 5%
    
    # 2. Entry
    entry_from = row['close']
    entry_to = row['close'] * 1.01 # 1% range
    
    # 3. TP
    # R = Entry - SL
    risk = entry_from - sl_level
    reward_1 = risk * 1.5
    reward_2 = risk * 2.5
    
    tp1 = entry_to + reward_1
    tp2 = entry_to + reward_2
    
    return {
        "entry_zone": {"from": round(entry_from, 2), "to": round(entry_to, 2)},
        "stop_loss": round(sl_level, 2),
        "take_profit_1": round(tp1, 2),
        "take_profit_2": round(tp2, 2),
        "invalidation": {"level": round(sl_level, 2), "type": "technical_support"},
        "key_reasons": [], # Filled by reporter based on score
        "risk_notes": []   # Filled by reporter
    }
