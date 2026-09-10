FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 (Pillow 의존성)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libwebp-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# data 디렉토리가 볼륨으로 마운트되므로 기본 파일만 미리 복사
RUN mkdir -p data static/images/photos

ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5000
ENV FLASK_DEBUG=false
# Docker 내부에서는 모니터 제어 불필요
ENV MONITOR_CONTROL=false

EXPOSE 5000

# gunicorn은 __main__ 블록을 실행하지 않으므로 모니터 스케줄러 없이 순수 Flask 앱만 동작
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "app:app"]
