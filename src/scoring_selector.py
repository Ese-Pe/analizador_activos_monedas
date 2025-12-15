"""
Scoring and Selection Agent
Scores coins and selects top opportunities
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CryptoSignal:
    """Structured crypto trading signal"""
    symbol: str
    name: str
    pair: str
    price: float
    market_cap: float
    volume_24h: float
    technical_score: float
    momentum_score: float
    volume_score: float
    risk_score: float
    final_score: float
    signals: Dict
    entry_zone: List[float]
    stop_loss: float
    target_1: float
    target_2: float
    btc_correlation: float
    timestamp: str
    
    def to_dict(self):
        return asdict(self)


class ScoringSelector:
    """Agent 3: Scoring and selection of top opportunities"""
    
    MIN_SCORE = 7.5
    MIN_MARKET_CAP = 100_000_000
    
    def __init__(self):
        self.output_file = "data/selected_cryptos.json"
    
    def market_cap_multiplier(self, market_cap: float) -> float:
        if market_cap > 10_000_000_000:
            return 1.1
        elif market_cap > 1_000_000_000:
            return 1.0
        elif market_cap > 100_000_000:
            return 0.95
        return 0.0
    
    def calculate_score(self, analysis: Dict) -> Dict:
        signals = analysis['signals']
        indicators = analysis['indicators']
        
        # Momentum (0-10)
        momentum = 2
        if signals['ema_aligned']:
            momentum += 4
        if signals['ema_cross']:
            momentum += 2
        if signals['rsi_bullish']:
            momentum += 2
        momentum_score = min(momentum, 10)
        
        # Volume (0-10)
        volume_score = 4
        if signals['volume_surge']:
            volume_score += 3
        if analysis['volume_24h'] > 50_000_000:
            volume_score += 3
        volume_score = min(volume_score, 10)
        
        # Technical (0-10)
        technical = 3
        if signals['macd_signal'] == 'buy':
            technical += 3
        if signals['trend'] == 'bullish':
            technical += 2
        if 40 <= signals['rsi_value'] <= 60:
            technical += 2
        technical_score = min(technical, 10)
        
        # Risk (0-10)
        atr_pct = indicators.get('atr_percent', 5)
        risk_score = max(0, 10 - (atr_pct * 1.2))
        
        final = (momentum_score * 0.35 + volume_score * 0.25 + technical_score * 0.25 + risk_score * 0.15)
        final *= self.market_cap_multiplier(analysis['market_cap'])
        
        return {
            "momentum_score": round(momentum_score, 2),
            "volume_score": round(volume_score, 2),
            "technical_score": round(technical_score, 2),
            "risk_score": round(risk_score, 2),
            "final_score": round(final, 2)
        }
    
    def calculate_levels(self, price: float, atr: float) -> Dict:
        # Stop loss: -2.5%
        stop_loss = price * 0.975
        # Targets: +10% and +20%
        target_1 = price * 1.10
        target_2 = price * 1.20
        # Entry zone: ±1.5%
        entry_low = price * 0.985
        entry_high = price * 1.015
        
        risk = price - stop_loss
        return {
            "entry_zone": [round(entry_low, 6), round(entry_high, 6)],
            "stop_loss": round(stop_loss, 6),
            "target_1": round(target_1, 6),
            "target_2": round(target_2, 6),
            "risk_reward_t1": round((target_1 - price) / risk, 2) if risk > 0 else 0
        }
    
    def select_top_opportunities(self, technical_data: Dict) -> List[CryptoSignal]:
        logger.info("=== Starting Scoring & Selection ===")
        scored_coins = []
        
        for analysis in technical_data['analyzed_coins']:
            if analysis['market_cap'] < self.MIN_MARKET_CAP:
                continue
            
            scores = self.calculate_score(analysis)
            
            if scores['final_score'] < self.MIN_SCORE:
                logger.info(f"  {analysis['symbol']}: Score {scores['final_score']:.1f} (below threshold)")
                continue
            
            atr = analysis['indicators'].get('atr', analysis['price'] * 0.02)
            levels = self.calculate_levels(analysis['price'], atr)
            
            signal = CryptoSignal(
                symbol=analysis['symbol'],
                name=analysis['name'],
                pair=f"{analysis['symbol']}/USDT",
                price=analysis['price'],
                market_cap=analysis['market_cap'],
                volume_24h=analysis['volume_24h'],
                technical_score=scores['technical_score'],
                momentum_score=scores['momentum_score'],
                volume_score=scores['volume_score'],
                risk_score=scores['risk_score'],
                final_score=scores['final_score'],
                signals=analysis['signals'],
                entry_zone=levels['entry_zone'],
                stop_loss=levels['stop_loss'],
                target_1=levels['target_1'],
                target_2=levels['target_2'],
                btc_correlation=0.75,
                timestamp=datetime.now().isoformat()
            )
            scored_coins.append(signal)
            logger.info(f"  ✓ {analysis['symbol']}: Score {scores['final_score']:.1f}")
        
        scored_coins.sort(key=lambda x: x.final_score, reverse=True)
        top_signals = scored_coins[:10]
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "market_context": technical_data.get('market_context', {}),
            "total_analyzed": len(technical_data['analyzed_coins']),
            "total_qualified": len(scored_coins),
            "top_opportunities": [s.to_dict() for s in top_signals]
        }
        
        os.makedirs('data', exist_ok=True)
        with open(self.output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"✓ Selection complete. {len(top_signals)} top opportunities identified.")
        return top_signals
