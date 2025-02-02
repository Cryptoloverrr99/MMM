from telegram import Bot, Update
from telegram.constants import ParseMode
from config import api_keys

class AlertEngine:
    def __init__(self):
        self.bot = Bot(token=api_keys.TELEGRAM_BOT_TOKEN)
        self.template = """
🚨 **Nouveau MEME Detecté** 🚨

• Token: [{symbol}]({url})
• Market Cap: ${mcap:,.0f} ↗️
• Liquidité: ${liq:,.0f} ({liq_lock}% Locked)
• Volume: ${volume:,.0f}/24h
• Holders: {holders} 👥
• Supply: {supply:,.0f} 💰

⚠️ **Checklist:**
- Dex Paid: {dex_paid}
- Dev Sold: {dev_sold}
- Top 10: {top10:.1%} (Max 35%)
- Dev Holding: {dev_holding:.1%} (Max 20%)
        """
        
    async def trigger_alert(self, token_data, checks):
        message = self.template.format(
            **token_data,
            dex_paid="✅ OUI" if checks['dex_paid'] else "❌ NON",
            dev_sold="✅ OUI" if checks['dev_sold'] else "❌ NON",
            top10=checks['top10'],
            dev_holding=checks['dev_holding']
        )
        
        await self.bot.send_message(
            chat_id=api_keys.TELEGRAM_CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
