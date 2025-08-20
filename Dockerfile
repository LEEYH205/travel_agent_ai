# 멀티스테이지 Dockerfile
# Stage 1: Python 백엔드 빌드
FROM python:3.11-slim as backend-builder

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 백엔드 소스 코드 복사
COPY travel_agent/backend/ ./travel_agent/backend/

# Stage 2: 백엔드 실행 환경
FROM python:3.11-slim as backend

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 백엔드 소스 코드 복사
COPY --from=backend-builder /app/travel_agent/backend/ ./travel_agent/backend/

# 캐시 디렉토리 생성
RUN mkdir -p cache logs

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# 포트 노출
EXPOSE 8000

# 헬스 체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 백엔드 실행
CMD ["uvicorn", "travel_agent.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 3: 프론트엔드 빌드
FROM node:18-alpine as frontend-builder

# 작업 디렉토리 설정
WORKDIR /app

# package.json 복사 및 의존성 설치
COPY package*.json ./
RUN npm ci --only=production

# 프론트엔드 소스 코드 복사
COPY travel_agent/frontend/ ./travel_agent/frontend/

# Stage 4: Nginx 기반 프론트엔드 서빙
FROM nginx:alpine as frontend

# Nginx 설정 복사
COPY nginx.conf /etc/nginx/nginx.conf

# 프론트엔드 빌드 결과 복사
COPY --from=frontend-builder /app/travel_agent/frontend/ /usr/share/nginx/html/

# 포트 노출
EXPOSE 80

# Stage 5: 개발 환경 (통합)
FROM python:3.11-slim as development

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치 (개발용 포함)
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# 소스 코드 복사
COPY . .

# 개발용 포트 노출
EXPOSE 8000 8501

# 개발 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=development

# 개발 서버 실행 (백엔드 + 프론트엔드)
CMD ["sh", "-c", "uvicorn travel_agent.backend.main:app --host 0.0.0.0 --port 8000 --reload & streamlit run travel_agent/frontend/app.py --server.port 8501 --server.address 0.0.0.0"]
