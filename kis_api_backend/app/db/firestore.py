"""Firestore 클라이언트 초기화 및 관리"""
from google.cloud import firestore
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Firestore 클라이언트 싱글톤
_firestore_client: Optional[firestore.Client] = None


def get_firestore_client() -> firestore.Client:
    """
    Firestore 클라이언트 인스턴스 반환 (Singleton 패턴)

    Google Cloud 기본 인증(ADC)을 사용:
    - 로컬: gcloud auth application-default login
    - Cloud Run: Service Account 자동 인증

    Returns:
        firestore.Client: Firestore 클라이언트 인스턴스
    """
    global _firestore_client

    if _firestore_client is None:
        try:
            # Project ID만 지정, credential은 자동 탐지 (ADC)
            _firestore_client = firestore.Client(project="kis-ai-485303")
            logger.info("Firestore client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise

    return _firestore_client


def get_firestore_db():
    """
    FastAPI 의존성 주입용 Firestore 클라이언트

    Yields:
        firestore.Client: Firestore 클라이언트 인스턴스
    """
    yield get_firestore_client()
