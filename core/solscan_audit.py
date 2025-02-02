class SolscanValidator:
    HOLDERS_API = "https://public-api.solscan.io/token/holders"
    BALANCE_API = "https://public-api.solscan.io/account/tokens"

    def __init__(self):
        self.session = aiohttp.ClientSession()
        
    async def analyze_token(self, token_address):
        holders = await self._get_holders(token_address)
        balance = await self._get_balance(token_address)
        
        return {
            'top10': self._calc_top10(holders),
            'dev_holding': self._parse_balance(balance),
            'dev_transfers': 0  # Non disponible sur API publique
        }

    async def _get_holders(self, address):
        async with self.session.get(
            self.HOLDERS_API,
            params={'tokenAddress': address}
        ) as resp:
            return await resp.json()

    async def _get_balance(self, address):
        async with self.session.get(
            self.BALANCE_API,
            params={'account': address}
        ) as resp:
            return await resp.json()
