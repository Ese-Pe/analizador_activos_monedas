"""
Technical Analysis Agent
Calculates indicators and generates signals
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """Agent 2: Technical analysis and indicator calculation"""
    
    def __init__(self):
        self.output_file = "data/technical_signals.json"
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        last_rsi = rsi.iloc[-1]
        return float(last_rsi) if pd.notna(last_rsi) else 50.0
    
    def calculate_macd(self, prices: pd.Series) -> Dict:
        if len(prices) < 26:
            return {"macd": 0, "signal": 0, "histogram": 0, "bullish": False}
        ema_12 = self.calculate_ema(prices, 12)
        ema_26 = self.calculate_ema(prices, 26)
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        return {
            "macd": float(macd_line.iloc[-1]) if pd.notna(macd_line.iloc[-1]) else 0,
            "signal": float(signal_line.iloc[-1]) if pd.notna(signal_line.iloc[-1]) else 0,
            "histogram": float(histogram.iloc[-1]) if pd.notna(histogram.iloc[-1]) else 0,
            "bullish": float(histogram.iloc[-1]) > 0 if pd.notna(histogram.iloc[-1]) else False
        }
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        if len(df) < period + 1:
            return 0.0
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        last_atr = atr.iloc[-1]
        return float(last_atr) if pd.notna(last_atr) else 0.0
    
    def detect_trend(self, prices: pd.Series) -> Dict:
        if len(prices) < 10:
            return {"trend": "neutral", "strength": 0}
        recent = prices.iloc[-10:]
        change_pct = ((recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0]) * 100
        if change_pct > 3:
            return {"trend": "bullish", "strength": min(abs(change_pct) / 5, 5)}
        elif change_pct < -3:
            return {"trend": "bearish", "strength": min(abs(change_pct) / 5, 5)}
        return {"trend": "neutral", "strength": 0}
    
    def analyze_coin(self, coin_data: Dict) -> Optional[Dict]:
        try:
            ohlc_data = coin_data.get('ohlc', [])
            if not ohlc_data or len(ohlc_data) < 20:
                return None
            
            df = pd.DataFrame(ohlc_data)
            for col in ['close', 'high', 'low', 'open']:
                df[col] = df[col].astype(float)
            
            prices = df['close']
            ema_7 = self.calculate_ema(prices, 7)
            ema_25 = self.calculate_ema(prices, 25)
            rsi = self.calculate_rsi(prices, 14)
            macd = self.calculate_macd(prices)
            atr = self.calculate_atr(df, 14)
            trend = self.detect_trend(prices)
            
            current_price = coin_data['current_price']
            current_ema_7 = float(ema_7.iloc[-1]) if pd.notna(ema_7.iloc[-1]) else current_price
            current_ema_25 = float(ema_25.iloc[-1]) if pd.notna(ema_25.iloc[-1]) else current_price
            
            volume_24h = coin_data.get('total_volume', 0)
            
            signals = {
                "ema_cross": current_ema_7 > current_ema_25,
                "ema_aligned": current_price > current_ema_7 > current_ema_25,
                "rsi_bullish": 35 <= rsi <= 70,
                "rsi_value": rsi,
                "macd_signal": "buy" if macd['bullish'] else "sell",
                "macd_histogram": macd['histogram'],
                "volume_surge": volume_24h > 10_000_000,
                "trend": trend['trend'],
                "trend_strength": trend['strength']
            }
            
            return {
                "symbol": coin_data['symbol'],
                "name": coin_data['name'],
                "price": current_price,
                "market_cap": coin_data['market_cap'],
                "volume_24h": volume_24h,
                "indicators": {
                    "ema_7": current_ema_7,
                    "ema_25": current_ema_25,
                    "rsi": rsi,
                    "macd": macd,
                    "atr": atr,
                    "atr_percent": (atr / current_price * 100) if current_price > 0 else 0
                },
                "signals": signals,
                "price_change_24h": coin_data.get('price_change_24h', 0),
                "price_change_7d": coin_data.get('price_change_7d', 0)
            }
        except Exception as e:
            logger.error(f"Error analyzing {coin_data.get('symbol', 'UNKNOWN')}: {e}")
            return None
    
    def analyze_all(self, crypto_data: Dict) -> Dict:
        logger.info("=== Starting Technical Analysis ===")
        analyzed_coins = []
        for coin_data in crypto_data['coins']:
            analysis = self.analyze_coin(coin_data)
            if analysis:
                analyzed_coins.append(analysis)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "market_context": crypto_data.get('market_context', {}),
            "analyzed_coins": analyzed_coins
        }
        
        os.makedirs('data', exist_ok=True)
        with open(self.output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"✓ Technical analysis complete. {len(analyzed_coins)} coins analyzed.")
        return result
