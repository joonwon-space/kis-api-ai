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

    def initialize(self):
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
            self._load_domestic_stocks()

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

    def _load_domestic_stocks(self):
        """
        국내 주식 데이터 로드

        먼저 기본 종목을 로드하고, 네이버 API로 추가 데이터를 시도합니다.
        """
        # 1. 기본 종목 데이터 먼저 로드 (필수)
        fallback_domestic = [
            # 대형주
            {"code": "005930", "name": "삼성전자"},
            {"code": "000660", "name": "SK하이닉스"},
            {"code": "035420", "name": "NAVER"},
            {"code": "035720", "name": "카카오"},
            {"code": "207940", "name": "삼성바이오로직스"},
            {"code": "005380", "name": "현대차"},
            {"code": "000270", "name": "기아"},
            {"code": "373220", "name": "LG에너지솔루션"},
            {"code": "068270", "name": "셀트리온"},
            {"code": "005490", "name": "POSCO홀딩스"},
            # 금융
            {"code": "105560", "name": "KB금융"},
            {"code": "055550", "name": "신한지주"},
            {"code": "086790", "name": "하나금융지주"},
            {"code": "323410", "name": "카카오뱅크"},
            {"code": "003540", "name": "대신증권"},
            # IT/게임
            {"code": "259960", "name": "크래프톤"},
            {"code": "036570", "name": "엔씨소프트"},
            {"code": "251270", "name": "넷마블"},
            {"code": "352820", "name": "하이브"},
            # 화학/소재
            {"code": "051910", "name": "LG화학"},
            {"code": "006400", "name": "삼성SDI"},
            {"code": "009830", "name": "한화솔루션"},
            # 자동차/부품
            {"code": "012330", "name": "현대모비스"},
            {"code": "161390", "name": "한국타이어앤테크놀로지"},
            # 바이오/제약
            {"code": "326030", "name": "SK바이오팜"},
            {"code": "128940", "name": "한미약품"},
            # 전자/반도체
            {"code": "066570", "name": "LG전자"},
            {"code": "009150", "name": "삼성전기"},
            # 기타
            {"code": "028260", "name": "삼성물산"},
            {"code": "032830", "name": "삼성생명"}
        ]

        for stock in fallback_domestic:
            self._index_domestic_stock(stock)

        logger.info(f"Loaded {len(fallback_domestic)} domestic stocks from fallback data")

        # 2. 네이버 API로 추가 데이터 로드 시도 (선택적)
        # 현재는 네트워크 문제로 비활성화
        # try:
        #     for keyword in ["삼성전자", "SK하이닉스"]:  # 샘플
        #         result = self._fetch_from_naver(keyword)
        #         if result:
        #             self._index_domestic_stock(result[0])
        # except Exception as e:
        #     logger.warning(f"Failed to fetch additional data from Naver: {e}")

    def _fetch_from_naver(self, keyword: str) -> List[Dict]:
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
            with httpx.Client() as client:
                response = client.get(url, params=params, timeout=5.0)
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

        캐시에 없으면 실시간으로 네이버 API를 호출합니다.

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

        # 5. 캐시에 없으면 실시간으로 네이버 API 호출 (국내 주식)
        logger.info(f"Stock not in cache, fetching from Naver: {keyword}")
        try:
            results = self._fetch_from_naver(keyword)
            if results:
                # 첫 번째 결과를 캐시에 추가하고 반환
                stock = results[0]
                self._index_domestic_stock(stock)
                logger.info(f"Found and cached: {stock['name']} ({stock['code']})")
                return self.cache["domestic"]["by_code"][stock["code"]]
        except Exception as e:
            logger.warning(f"Failed to fetch from Naver in real-time: {e}")

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
