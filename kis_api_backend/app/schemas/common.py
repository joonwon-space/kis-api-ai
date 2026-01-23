"""공통 스키마 정의"""
from enum import Enum


class MarketType(str, Enum):
    """시장 구분"""
    ALL = "ALL"
    DOMESTIC = "DOMESTIC"
    OVERSEAS = "OVERSEAS"


class Currency(str, Enum):
    """통화 구분"""
    KRW = "KRW"
    USD = "USD"
