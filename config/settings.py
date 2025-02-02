from decimal import Decimal

class Filters:
    MAX_SUPPLY = Decimal('1e9')
    MIN_MCAP = Decimal('150000')
    MIN_LIQUIDITY = Decimal('90000')
    LIQ_LOCK = Decimal('99')
    MAX_DEV_HOLDING = Decimal('0.20')
    MAX_TOP10 = Decimal('0.35')
    MIN_MARKERS = 200
    MIN_HOLDERS = 100
    MIN_VOLUME = Decimal('500000')
    MCAP_INCREASE = Decimal('50000')
