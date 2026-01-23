"""종목 마스터 데이터 관리 서비스"""
import httpx
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class StockMasterService:
    """
    종목 마스터 데이터 캐싱 및 검색 서비스

    네이버 금융 API에서 종목 데이터를 가져와 메모리에 캐싱하고,
    빠른 검색을 위한 인덱스를 제공합니다.
    """

    def __init__(self):
        self.cache = {
            "domestic": {
                "by_code": {},
                "by_name": {}
            },
            "overseas": {
                "by_symbol": {},
                "by_name": {}
            },
            "last_updated": None
        }
        self._initialized = False

    async def initialize(self):
        """
        종목 데이터 초기화

        외부 API에서 종목 데이터를 다운로드하고 캐시를 구축합니다.
        """
        if self._initialized:
            logger.info("Stock master already initialized")
            return

        try:
            logger.info("Initializing stock master data...")

            # 국내 주식 데이터 로드
            await self._load_domestic_stocks()

            # 해외 주식 데이터 로드 (기본 주요 종목만)
            self._load_overseas_stocks()

            self.cache["last_updated"] = datetime.now().isoformat()
            self._initialized = True

            logger.info(f"Stock master initialized: "
                       f"{len(self.cache['domestic']['by_code'])} domestic, "
                       f"{len(self.cache['overseas']['by_symbol'])} overseas stocks")
        except Exception as e:
            logger.error(f"Failed to initialize stock master: {e}")
            # 초기화 실패 시에도 기본 데이터로 동작 가능하도록
            self._load_fallback_data()

    async def _load_domestic_stocks(self):
        """
        국내 주식 데이터 로드

        네이버 금융 자동완성 API를 활용하여 주요 종목 데이터를 수집합니다.
        """
        # 주요 종목 리스트 (코스피 200 주요 종목)
        major_stocks = [
            "삼성전자", "SK하이닉스", "NAVER", "카카오", "삼성바이오로직스",
            "현대차", "기아", "LG에너지솔루션", "셀트리온", "POSCO홀딩스",
            "KB금융", "신한지주", "LG화학", "삼성SDI", "현대모비스",
            "기업은행", "하나금융지주", "삼성생명", "삼성물산", "LG전자"
        ]

        for keyword in major_stocks:
            try:
                result = await self._fetch_from_naver(keyword)
                if result:
                    self._index_domestic_stock(result[0])  # 첫 번째 결과 사용
            except Exception as e:
                logger.warning(f"Failed to fetch {keyword}: {e}")
                continue

    async def _fetch_from_naver(self, keyword: str) -> List[Dict]:
        """
        네이버 금융 API로 종목 검색

        Args:
            keyword: 검색 키워드

        Returns:
            List[Dict]: 검색 결과 리스트
        """
        url = "https://ac.finance.naver.com/ac"
        params = {
            "q": keyword,
            "q_enc": "utf-8",
            "st": "111",
            "frm": "stock",
            "r_format": "json"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=5.0)
                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("items", [[]])[0]:
                    if "|" in item:
                        parts = item.split("|")
                        code = parts[0]
                        name = parts[1]
                        # 종목코드가 6자리 숫자인 경우만 (정규 주식)
                        if code.isdigit() and len(code) == 6:
                            results.append({"code": code, "name": name})

                return results
        except Exception as e:
            logger.error(f"Failed to fetch from Naver: {e}")
            return []

    def _index_domestic_stock(self, stock: Dict):
        """
        국내 주식을 인덱스에 추가

        Args:
            stock: 종목 정보 {"code": "005930", "name": "삼성전자"}
        """
        code = stock["code"]
        name = stock["name"]

        self.cache["domestic"]["by_code"][code] = {
            "code": code,
            "name": name,
            "market": "DOMESTIC"
        }

        # 종목명으로도 검색 가능하도록
        self.cache["domestic"]["by_name"][name] = code
        self.cache["domestic"]["by_name"][name.upper()] = code

    def _load_overseas_stocks(self):
        """
        해외 주식 데이터 로드 (하드코딩)

        주요 미국 주식만 포함합니다.
        """
        major_us_stocks = [
            {"symbol": "AAPL", "name": "Apple Inc."},
            {"symbol": "MSFT", "name": "Microsoft Corporation"},
            {"symbol": "GOOGL", "name": "Alphabet Inc."},
            {"symbol": "AMZN", "name": "Amazon.com Inc."},
            {"symbol": "TSLA", "name": "Tesla Inc."},
            {"symbol": "META", "name": "Meta Platforms Inc."},
            {"symbol": "NVDA", "name": "NVIDIA Corporation"},
            {"symbol": "AMD", "name": "Advanced Micro Devices Inc."},
            {"symbol": "NFLX", "name": "Netflix Inc."},
            {"symbol": "DIS", "name": "Walt Disney Company"}
        ]

        for stock in major_us_stocks:
            symbol = stock["symbol"]
            name = stock["name"]

            self.cache["overseas"]["by_symbol"][symbol] = {
                "symbol": symbol,
                "name": name,
                "market": "OVERSEAS",
                "exchange": "NASD"
            }

            # 심볼과 이름으로 검색 가능
            self.cache["overseas"]["by_name"][symbol] = symbol
            self.cache["overseas"]["by_name"][symbol.upper()] = symbol
            self.cache["overseas"]["by_name"][name.upper()] = symbol

    def _load_fallback_data(self):
        """
        Fallback 데이터 로드

        외부 API 실패 시 최소한의 주요 종목만 제공합니다.
        """
        # 최소한의 국내 주요 종목
        fallback_domestic = [
            {"code": "005930", "name": "삼성전자"},
            {"code": "000660", "name": "SK하이닉스"},
            {"code": "035420", "name": "NAVER"}
        ]

        for stock in fallback_domestic:
            self._index_domestic_stock(stock)

        # 해외 주식은 _load_overseas_stocks()로 처리
        self._load_overseas_stocks()

        self.cache["last_updated"] = datetime.now().isoformat()
        self._initialized = True
        logger.warning("Loaded fallback stock data")

    def search(self, keyword: str) -> Optional[Dict]:
        """
        종목 검색

        Args:
            keyword: 검색 키워드 (종목명 또는 코드/심볼)

        Returns:
            Dict: 종목 정보 또는 None
            {
                "market": "DOMESTIC",
                "symbol": "005930",
                "name": "삼성전자",
                "exchange": "KRX"  # 해외 주식의 경우
            }
        """
        if not self._initialized:
            logger.warning("Stock master not initialized, searching anyway")

        keyword_upper = keyword.upper().strip()

        # 1. 국내 주식 검색 (코드)
        if keyword in self.cache["domestic"]["by_code"]:
            return self.cache["domestic"]["by_code"][keyword]

        # 2. 국내 주식 검색 (종목명)
        if keyword_upper in self.cache["domestic"]["by_name"]:
            code = self.cache["domestic"]["by_name"][keyword_upper]
            return self.cache["domestic"]["by_code"][code]

        # 3. 해외 주식 검색 (심볼)
        if keyword_upper in self.cache["overseas"]["by_symbol"]:
            return self.cache["overseas"]["by_symbol"][keyword_upper]

        # 4. 해외 주식 검색 (이름)
        if keyword_upper in self.cache["overseas"]["by_name"]:
            symbol = self.cache["overseas"]["by_name"][keyword_upper]
            return self.cache["overseas"]["by_symbol"][symbol]

        return None

    def get_stats(self) -> Dict:
        """
        캐시 통계 조회

        Returns:
            Dict: 통계 정보
        """
        return {
            "domestic_count": len(self.cache["domestic"]["by_code"]),
            "overseas_count": len(self.cache["overseas"]["by_symbol"]),
            "last_updated": self.cache["last_updated"],
            "initialized": self._initialized
        }


# 전역 인스턴스 (싱글톤)
stock_master_service = StockMasterService()
