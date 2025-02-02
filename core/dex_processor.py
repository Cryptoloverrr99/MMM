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
            return self._sanitize_data(data['data'])
    
    def _sanitize_data(self, raw_data):
        return [{
            'address': t['address'],
            'symbol': t['symbol'],
            'mcap': Decimal(t.get('marketCap', 0)),
            'liq': Decimal(t.get('liquidity', 0)),
            'volume': Decimal(t.get('volume24h', 0)),
            'holders': t.get('holders', 0),
            'supply': Decimal(t.get('totalSupply', 0)),
            'url': f"https://dexscreener.com/solana/{t['address']}"
        } for t in raw_data]
