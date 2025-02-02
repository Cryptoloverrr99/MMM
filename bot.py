import asyncio
import aiosqlite
from decimal import Decimal
from core.dex_processor import DexScanner
from core.solscan_audit import SolscanValidator
from core.alert_system import AlertEngine
from config.settings import Filters

class MemeTrackerBot:
    def __init__(self):
        self.dex = DexScanner()
        self.solscan = SolscanValidator(api_keys.SOLSCAN_API_KEY)
        self.alerter = AlertEngine()
        self.db_path = "data/processed.db"
        
    async def run(self):
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            
            while True:
                tokens = await self.dex.fetch_tokens()
                for token in tokens:
                    if not await self._is_processed(db, token['address']):
                        await self._process_token(db, token)
                
                await asyncio.sleep(120)  # 2 minutes
                
    async def _process_token(self, db, token):
        audit = await self.solscan.analyze_token(token['address'])
        
        if self._passes_filters(token, audit):
            await self.alerter.trigger_alert(token, {
                'dex_paid': False,  # À implémenter selon données
                'dev_sold': audit['dev_sold'] > Decimal('0.01'),
                'top10': audit['top10'],
                'dev_holding': audit['dev_holding']
            })
            
        await self._mark_processed(db, token['address'])
    
    def _passes_filters(self, token, audit):
        checks = [
            token['supply'] <= Filters.MAX_SUPPLY,
            token['mcap'] >= Filters.MIN_MCAP,
            token['liq'] >= Filters.MIN_LIQUIDITY,
            audit['top10'] <= Filters.MAX_TOP10,
            audit['dev_holding'] <= Filters.MAX_DEV_HOLDING,
            token['holders'] >= Filters.MIN_HOLDERS,
            token['volume'] >= Filters.MIN_VOLUME,
            audit['dev_transfers'] == 0,
            audit['dev_sold'] < Decimal('0.01')
        ]
        return all(checks)
    
    async def _init_db(self, db):
        await db.execute('''CREATE TABLE IF NOT EXISTS processed 
                          (address TEXT PRIMARY KEY)''')
    
    async def _is_processed(self, db, address):
        cursor = await db.execute("SELECT 1 FROM processed WHERE address=?", (address,))
        return await cursor.fetchone() is not None
    
    async def _mark_processed(self, db, address):
        await db.execute("INSERT INTO processed VALUES (?)", (address,))
        await db.commit()

if __name__ == "__main__":
    bot = MemeTrackerBot()
    asyncio.run(bot.run())
