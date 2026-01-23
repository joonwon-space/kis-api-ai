"""커스텀 예외 정의"""


class KISAPIError(Exception):
    """KIS API 관련 기본 예외"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class TokenExpiredError(KISAPIError):
    """토큰 만료 예외"""
    pass


class InvalidAccountError(KISAPIError):
    """유효하지 않은 계좌 정보"""
    pass


class InsufficientBalanceError(KISAPIError):
    """잔고 부족 예외"""
    pass


class OrderFailedError(KISAPIError):
    """주문 실패 예외"""
    pass
