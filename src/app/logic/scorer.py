import pandas as pd
import numpy as np
from typing import Dict, List, Any

class Scorer:
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {
            "trend": 0.22,
            "base": 0.20,
            "breakout": 0.22,
            "volume": 0.18,
            "momentum": 0.10,
            "risk": 0.08
        }
    
    def calculate_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate score for the *latest* bar in the dataframe.
        Assumes df has indicators calculated.
        """
        if df.empty or len(df) < 50: # Minimum data check
            return {"score_total": 0, "breakdown": {}}
            
        row = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 1. Trend (0-100)
        # Price > EMA20 > EMA50 -> Strong Trend
        trend_score = 0
        if row['close'] > row['ema20'] > row['ema50']:
            trend_score = 100
        elif row['close'] > row['ema50']:
            trend_score = 60
        else:
            trend_score = 0
            
        # Slope check (proxy: EMA20 > EMA20[prev])
        if row['ema20'] > prev['ema20']:
             trend_score += 10 # Bonus for rising
        trend_score = min(100, trend_score)

        # 2. Base (Squeeze) (0-100)
        # Low BB width or ATR compression implies base
        # BB width < 0.10 (10%) is decent for VN30? Or relative to recent average?
        # Let's use relative width: Current Width / Avg Width(20)
        avg_width = df['bb_width'].rolling(20).mean().iloc[-1]
        base_score = 0
        if avg_width > 0:
            compression = row['bb_width'] / avg_width
            if compression < 0.8: # Squeezing
                base_score = 100
            elif compression < 1.0:
                base_score = 70
            else:
                base_score = 30
        
        # 3. Breakout (0-100)
        # Price near high_20 or breaking out
        breakout_score = 0
        pivot_high = row['high_20']
        if row['close'] >= pivot_high * 0.98: # Near breakout
             breakout_score = 80
        if row['close'] > pivot_high: # New high (signal might depend on this being a breakout confirmed)
             breakout_score = 100
        
        # 4. Volume (0-100)
        # High relative volume
        vol_score = 0
        vol_rel = row['volume'] / row['vol_ma20'] if row['vol_ma20'] > 0 else 0
        if vol_rel > 1.5:
            vol_score = 100
        elif vol_rel > 1.0:
            vol_score = 70
        else:
            vol_score = 40
            
        # 5. Momentum (0-100) - RSI
        mom_score = 0
        rsi = row['rsi']
        if 50 <= rsi <= 70: # Bullish zone
            mom_score = 100
        elif rsi > 70: # Overbought but strong
            mom_score = 60
        elif 40 <= rsi < 50:
            mom_score = 40
        else:
            mom_score = 0
            
        # 6. Risk (0-100)
        # Distance to Stop Loss (e.g. EMA20) relative to volatility (ATR)
        # Closer stop = lower risk = higher score
        stop_level = row['ema20'] # Simplified SL
        dist = (row['close'] - stop_level) / stop_level
        atr_rel = row['atr'] / row['close']
        
        risk_score = 50
        if dist < atr_rel: # Tight stop (less than 1 ATR)
            risk_score = 100
        elif dist < 2 * atr_rel:
            risk_score = 70
        
        # Weighted Sum
        w = self.weights
        total = (
            trend_score * w['trend'] +
            base_score * w['base'] +
            breakout_score * w['breakout'] +
            vol_score * w['volume'] +
            mom_score * w['momentum'] +
            risk_score * w['risk']
        )
        
        # Penalties
        penalties = []
        # Overextended: Close > EMA20 + 2*ATR
        if row['close'] > row['ema20'] + 2 * row['atr']:
            total -= 10
            penalties.append({"type": "overextended", "value": -10})
        
        # Gap risk (simplified: today low > prev high + atr?)
        # Skipping simple gap check for now without robust data
        
        total = max(0, min(100, total))
        
        return {
            "score_total": round(total, 2),
            "breakdown": {
                "trend": trend_score,
                "base": base_score,
                "breakout": breakout_score,
                "volume": vol_score,
                "momentum": mom_score,
                "risk": risk_score
            },
            "penalties": penalties,
            "row": row.to_dict() # debug info
        }
