# Stage 1: Builder - 의존성 설치
FROM python:3.11-slim as builder

WORKDIR /app

# 의존성 파일만 먼저 복사 (레이어 캐싱 최적화)
COPY requirements.txt .

# 의존성 설치 (사용자 디렉토리에 설치)
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime - 최종 이미지
FROM python:3.11-slim

WORKDIR /app

# Non-root 유저 생성
RUN adduser --disabled-password --gecos "" appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# 빌더 스테이지에서 설치된 패키지 복사
COPY --from=builder /root/.local /home/appuser/.local

# 소스 코드 복사 (appuser 소유로 설정)
COPY --chown=appuser:appuser . .

# PATH에 사용자 bin 디렉토리 추가
ENV PATH=/home/appuser/.local/bin:$PATH

# Non-root 유저로 전환
USER appuser

# 포트 노출
EXPOSE 8000

# 헬스 체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
