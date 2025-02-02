import aiohttp
from decimal import Decimal
from config.settings import Filters

class DexScanner:
    API_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
    
    def __init__(self):
        self.session = aiohttp.ClientSession()
        
    async def fetch_tokens(self):
        async with self.session.get(self.API_URL) as resp:
            data = await resp.json()
            return self._process_data(data['data'])
    
    def _process_data(self, raw_tokens):
        processed = []
        for t in raw_tokens:
            processed.append({
                'address': t['address'],
                'symbol': t['symbol'],
                'mcap': Decimal(t.get('marketCap', 0)),
                'liq': Decimal(t.get('liquidity', 0)),
                'volume': Decimal(t.get('volume24h', 0)),
                'holders': t.get('holders', 0),
                'supply': Decimal(t.get('totalSupply', 0)),
                'locked_liq_pct': self._calc_locked_pct(t),
                'markers': t.get('analysis', {}).get('markers', 0),
                'url': f"https://dexscreener.com/solana/{t['address']}",
                'previous_mcap': Decimal(0)
            })
        return processed
    
    def _calc_locked_pct(self, token_data):
        locked = Decimal(token_data.get('lockedLiquidity', 0))
        total = Decimal(token_data.get('liquidity', 1))  # Éviter division par 0
        return (locked / total * 100) if total > 0 else Decimal(0)
