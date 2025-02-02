import aiohttp
from decimal import Decimal

class SolscanValidator:
    HOLDERS_API = "https://pro-api.solscan.io/v2.0/token/holders"
    BALANCE_API = "https://pro-api.solscan.io/v2.0/account/balance_change"
    
    def __init__(self, api_key):
        self.headers = {'X-API-KEY': api_key}
        self.session = aiohttp.ClientSession(headers=self.headers)
        
    async def analyze_token(self, token_address):
        holders = await self._get_holders(token_address)
        dev_activity = await self._get_dev_activity(token_address)
        
        return {
            'top10': self._calc_top10(holders),
            'dev_holding': dev_activity['holding'],
            'dev_sold': dev_activity['sold'],
            'dev_transfers': dev_activity['transfers']
        }
    
    async def _get_holders(self, address):
        async with self.session.get(self.HOLDERS_API, params={'token': address}) as resp:
            return await resp.json()
    
    async def _get_dev_activity(self, address):
        async with self.session.get(self.BALANCE_API, params={'token': address}) as resp:
            data = await resp.json()
            return {
                'holding': Decimal(data.get('devHolding', 0)),
                'sold': Decimal(data.get('soldFirst10', 0)),
                'transfers': data.get('transferCount', 0)
            }
    
    def _calc_top10(self, holders_data):
        top10 = sum(h['amount'] for h in holders_data['data'][:10])
        total = holders_data['total']
        return Decimal(top10) / Decimal(total)
