import asyncio
import aiosqlite
from decimal import Decimal
from datetime import datetime
from core.dex_processor import DexScanner
from core.solscan_audit import SolscanValidator
from core.alert_system import AlertEngine
from config.settings import Filters
from config import api_keys

class MemeTrackerBot:
    def __init__(self):
        self.dex = DexScanner()
        self.solscan = SolscanValidator()
        self.alerter = AlertEngine()
        self.db_path = "data/processed.db"
        
    async def __ainit__(self):
        """Initialisation asynchrone"""
        self.db = await aiosqlite.connect(self.db_path)
        await self._init_tables()
        return self
        
    async def __adel__(self):
        """Nettoyage asynchrone"""
        await self.db.close()
        await self.dex.session.close()
        await self.solscan.session.close()

    async def _init_tables(self):
        """Crée les tables de suivi"""
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS processed (
                address TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS mcap_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT,
                mcap DECIMAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await self.db.commit()

    async def run(self):
        async with self:
            while True:
                try:
                    tokens = await self.dex.fetch_tokens()
                    for token in tokens:
                        if not await self._is_processed(token['address']):
                            await self._process_token(token)
                    await asyncio.sleep(120)
                except Exception as e:
                    print(f"Erreur critique: {str(e)}")
                    break

    async def __aenter__(self):
        return await self.__ainit__()
    
    async def __aexit__(self, *args):
        await self.__adel__()

    async def _is_processed(self, address):
        """Vérifie si le token est déjà traité"""
        cursor = await self.db.execute(
            "SELECT 1 FROM processed WHERE address = ?", 
            (address,)
        )
        return await cursor.fetchone() is not None

    async def _process_token(self, token):
        """Traite un nouveau token"""
        # Suivi du MCap
        mcap_increase = await self._track_mcap(token)
        token['mcap_increase'] = mcap_increase
        
        # Audit Solscan
        audit = await self.solscan.analyze_token(token['address'])
        
        # Vérification des conditions
        if self._passes_filters(token, audit):
            await self.alerter.trigger_alert(token, {
                'dex_paid': False,  # À implémenter
                'dev_sold': audit.get('dev_sold', Decimal(0)),
                **audit
            })
            
        # Marquer comme traité
        await self.db.execute(
            "INSERT INTO processed (address) VALUES (?)",
            (token['address'],)
        )
        await self.db.commit()

    async def _track_mcap(self, token):
        """Suivi de l'évolution du Market Cap"""
        cursor = await self.db.execute(
            """SELECT mcap FROM mcap_history 
            WHERE address = ? 
            ORDER BY timestamp DESC LIMIT 1""",
            (token['address'],)
        )
        last = await cursor.fetchone()
        
        current_mcap = token['mcap']
        await self.db.execute(
            "INSERT INTO mcap_history (address, mcap) VALUES (?, ?)",
            (token['address'], float(current_mcap))
        )
        await self.db.commit()
        
        return current_mcap - Decimal(last[0]) if last else Decimal(0)

    def _passes_filters(self, token, audit):
        """Vérifie tous les critères de filtrage"""
        return all([
            # Conditions Dexscreener
            token['supply'] <= Filters.MAX_SUPPLY,
            token['mcap'] >= Filters.MIN_MCAP,
            token['liq'] >= Filters.MIN_LIQUIDITY,
            token['locked_liq_pct'] >= Filters.LIQ_LOCK,
            token['markers'] >= Filters.MIN_MARKERS,
            token['holders'] >= Filters.MIN_HOLDERS,
            token['volume'] >= Filters.MIN_VOLUME,
            token['mcap_increase'] >= Filters.MCAP_INCREASE,
            
            # Conditions Solscan
            audit.get('top10', Decimal(1)) <= Filters.MAX_TOP10,
            audit.get('dev_holding', Decimal(1)) <= Filters.MAX_DEV_HOLDING,
            audit.get('dev_transfers', 1) == 0,
            audit.get('dev_sold', Decimal(1)) < Decimal('0.01'),
            
            # Condition supplémentaire
            not self._check_rugpull_indicators(token, audit)
        ])

    def _check_rugpull_indicators(self, token, audit):
        """Détection avancée de rugpulls"""
        return any([
            audit.get('dev_transfers', 0) > 0,
            token['locked_liq_pct'] < 90,
            token['mcap'] > 1000000 and token['holders'] < 50
        ])

if __name__ == "__main__":
    async def main():
        async with MemeTrackerBot() as bot:
            try:
                await bot.run()
            except KeyboardInterrupt:
                print("\n🔴 Bot arrêté proprement")
                
    asyncio.run(main())
