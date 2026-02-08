import logging
import httpx
from src.app.core.config import settings

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    async def send_message(self, text: str):
        """
        Send a text message to the configured chat.
        """
        if not self.token or not self.chat_id:
            logger.warning("Telegram token or chat_id not configured. Skipping message.")
            return

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=10.0)
                resp.raise_for_status()
                logger.info("Telegram message sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    async def send_report(self, top3: list, run_id: str):
        """
        Format and send the Top 3 analysis report.
        """
        if not top3:
            await self.send_message(f"📉 *Market Update*: Analysis `{run_id}` completed. No high-conviction setups found today.")
            return

        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines = [f"👔 **VN30 EXECUTIVE BRIEFING**"]
        lines.append(f"🗓 *{now_str}* | Run: `{str(run_id)[:8]}`")
        lines.append("")
        lines.append("**TOP HIGH-CONVICTION SETUPS**")

        lines.append("─" * 20)

        for i, item in enumerate(top3):
            sym = item['symbol']
            score = float(item['score_total'])
            signal = item.get('signal', {})
            breakdown = item.get('breakdown', {})
            
            # Determine Action based on score
            action = "WATCH"
            if score >= 80: action = "STRONG BUY"
            elif score >= 60: action = "BUY"
            elif score >= 50: action = "ACCUMULATE"
            
            icon = ["🥇", "🥈", "🥉"][i] if i < 3 else "🔹"
            
            lines.append(f"{icon} **{sym}**")
            lines.append(f"📈 **{action}** (Score: {score}/100)")
            
            # Trade Plan
            if signal:
                entry = signal.get('entry_zone', {})
                low = entry.get('from', entry.get('min', 0))
                high = entry.get('to', entry.get('max', 0))
                tp1 = signal.get('take_profit_1', 0)
                tp2 = signal.get('take_profit_2', 0)
                sl = signal.get('stop_loss', 0)
                
                lines.append(f"• **Entry**: {low:,.0f} - {high:,.0f}")
                lines.append(f"• **Targets**: {tp1:,.0f} | {tp2:,.0f}")
                lines.append(f"• **Stop**: {sl:,.0f}")
            
            # Thesis (Drivers)
            reasons = []
            if breakdown.get('trend', 0) > 15: reasons.append("Strong Trend")
            if breakdown.get('volume', 0) > 10: reasons.append("Vol Spike")
            if breakdown.get('momentum', 0) > 10: reasons.append("RSI Bullish")
            if breakdown.get('breakout', 0) > 0: reasons.append("Breakout")
            
            if reasons:
                lines.append(f"💡 *Thesis: {', '.join(reasons)}*")
            
            lines.append("")

        lines.append("⚠️ *Disclaimer: AI-generated analysis for reference only.*")
        
        msg = "\n".join(lines)
        await self.send_message(msg)
