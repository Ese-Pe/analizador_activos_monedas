"""
Telegram Notifier Agent
Sends trading signals and alerts via Telegram
"""

import os
import logging
from datetime import datetime
from typing import Dict
import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send notifications via Telegram"""
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    def send_message(self, text: str, parse_mode: str = "Markdown"):
        """Send a message to Telegram"""
        if not self.token or not self.chat_id:
            logger.warning("⚠️ Telegram credentials not configured")
            return False
        
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            logger.info("✓ Telegram notification sent")
            return True
        except Exception as e:
            logger.error(f"❌ Error sending Telegram message: {e}")
            return False
    
    def format_mcap(self, mcap: float) -> str:
        """Format market cap"""
        if mcap >= 1_000_000_000:
            return f"${mcap/1_000_000_000:.1f}B"
        else:
            return f"${mcap/1_000_000:.0f}M"
    
    def format_signal_telegram(self, signal: Dict, rank: int) -> str:
        """Format a signal for Telegram"""
        medal = ["🥇", "🥈", "🥉"][rank-1] if rank <= 3 else f"#{rank}"
        
        entry_low, entry_high = signal['entry_zone']
        price = signal['price']
        stop_loss = signal['stop_loss']
        target_1 = signal['target_1']
        target_2 = signal['target_2']
        
        risk_pct = ((price - stop_loss) / price * 100)
        reward_pct_t1 = ((target_1 - price) / price * 100)
        reward_pct_t2 = ((target_2 - price) / price * 100)
        
        # Format signals
        signals_list = []
        if signal['signals'].get('ema_aligned'):
            signals_list.append("EMA✓")
        if signal['signals'].get('rsi_bullish'):
            signals_list.append(f"RSI{signal['signals'].get('rsi_value', 0):.0f}")
        if signal['signals'].get('macd_signal') == 'buy':
            signals_list.append("MACD✓")
        if signal['signals'].get('volume_surge'):
            signals_list.append("Vol✓")
        
        signals_str = " | ".join(signals_list[:4]) if signals_list else "N/A"
        
        return f"""
{medal} *{signal['symbol']}* ({signal['name']})
━━━━━━━━━━━━━━━━━━━━
📊 Score: *{signal['final_score']:.1f}/10*
💰 Precio: ${price:,.4f}
📈 Cap: {self.format_mcap(signal['market_cap'])}

🎯 Entry: ${entry_low:,.4f} - ${entry_high:,.4f}
🛑 Stop: ${stop_loss:,.4f} (-{risk_pct:.1f}%)
💎 T1: ${target_1:,.4f} (+{reward_pct_t1:.1f}%)
💎 T2: ${target_2:,.4f} (+{reward_pct_t2:.1f}%)

✅ Señales: {signals_str}
"""
    
    def send_analysis_report(self, data: Dict):
        """Send complete analysis report via Telegram"""
        signals = data.get('top_opportunities', [])
        market_ctx = data.get('market_context', {})
        
        # Header
        header = f"""
🪙 *CRYPTO SWING TRADING*
📅 {datetime.now().strftime('%d %b %Y, %H:%M')} CET

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 *CONTEXTO DE MERCADO*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔸 BTC Dominance: {market_ctx.get('btc_dominance', 0):.1f}%
💰 Total Market Cap: {self.format_mcap(market_ctx.get('total_market_cap', 0))}
✅ {data.get('total_qualified', 0)} cryptos calificadas de {data.get('total_analyzed', 0)} analizadas
"""
        self.send_message(header)
        
        if signals:
            # Send header for opportunities
            self.send_message("━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🏆 *TOP OPORTUNIDADES*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            # Send top 3 signals
            for i, signal in enumerate(signals[:3], 1):
                msg = self.format_signal_telegram(signal, i)
                self.send_message(msg)
            
            # Footer if more signals
            if len(signals) > 3:
                footer = f"\n📋 +{len(signals)-3} oportunidades más disponibles"
                self.send_message(footer)
        else:
            self.send_message("⚠️ *No se encontraron oportunidades* que cumplan los criterios de scoring esta semana.\n\nEl mercado puede estar en fase lateral o sin señales claras.")
    
    def send_high_score_alert(self, signal):
        """Send alert for high-score signals (>=8.5)"""
        if signal.final_score < 8.5:
            return
        
        price = signal.price
        target_1 = signal.target_1
        reward_pct = ((target_1 - price) / price * 100)
        
        alert = f"""
🚨 *ALERTA DE ALTA PUNTUACIÓN*

*{signal.symbol}* ({signal.name})
⭐ Score: *{signal.final_score:.1f}/10*

💰 ${price:,.4f}
🎯 Target 1: ${target_1:,.4f} (+{reward_pct:.1f}%)

🔥 Oportunidad excepcional detectada
"""
        self.send_message(alert)
