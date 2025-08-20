# 🚀 Travel Agent AI 클라우드 배포 가이드

## 📋 개요
이 문서는 Travel Agent AI를 Streamlit Cloud와 Hugging Face Spaces에 배포하는 방법을 설명합니다.

## 🌐 **1단계: Streamlit Cloud 배포 (프론트엔드)**

### 1.1 Streamlit Cloud 접속
- [Streamlit Cloud](https://share.streamlit.io/)에 접속
- GitHub 계정으로 로그인

### 1.2 새 앱 생성
1. **"New app"** 버튼 클릭
2. **Repository**: `LEEYH205/travel_agent_ai` 선택
3. **Branch**: `main` 선택
4. **Main file path**: `travel_agent/frontend/app.py` 입력
5. **App URL**: 원하는 URL 설정 (예: `travel-agent-ai`)

### 1.3 환경 변수 설정
**Secrets** 섹션에서 다음 환경 변수 설정:

```toml
# 백엔드 URL만 설정 (API 키는 백엔드에서 관리)
BACKEND_URL = "https://your-huggingface-spaces-url.com"

# 환경 설정
APP_ENV = "production"
DEFAULT_LOCALE = "ko_KR"
```

**중요**: API 키는 백엔드 환경 변수에서 관리됩니다. 프론트엔드는 백엔드만 호출하는 프록시 패턴을 사용합니다.

### 1.4 배포 실행
- **"Deploy!"** 버튼 클릭
- 배포 완료까지 2-3분 대기

---

## 🤗 **2단계: Hugging Face Spaces 배포 (백엔드)**

### 2.1 Hugging Face Spaces 접속
- [Hugging Face Spaces](https://huggingface.co/spaces)에 접속
- 계정 생성 또는 로그인

### 2.2 새 Space 생성
1. **"Create new Space"** 버튼 클릭
2. **Space name**: `travel-agent-ai-backend` 입력
3. **Space SDK**: `Gradio` 선택
4. **Space hardware**: `CPU` 선택 (무료)
5. **License**: `MIT` 선택

### 2.3 파일 업로드
다음 파일들을 Space에 업로드:
- `app.py` (프로젝트 루트의 파일)
- `requirements-huggingface.txt`
- `travel_agent/` 폴더 전체

### 2.4 환경 변수 설정
**Settings** → **Repository secrets**에서:
```
OPENAI_API_KEY = "sk-proj-..."
OPENWEATHER_API_KEY = "df624c4b28cd5be046824a2c38ce8469"
GOOGLE_MAPS_API_KEY = "AIzaSyBepFNHq9AQAIuIDQl2DO0pQ2_TKZ_BUdE"
FOURSQUARE_API_KEY = "your_foursquare_key"
TAVILY_API_KEY = "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"
```

### 2.5 배포 확인
- Space가 자동으로 빌드 및 배포됨
- **App** 탭에서 API 엔드포인트 확인

---

## 🔗 **3단계: 프론트엔드-백엔드 연결**

### 3.1 백엔드 프록시 패턴
이 시스템은 **백엔드 프록시 패턴**을 사용합니다:

- **프론트엔드**: API 키 입력 없음, 백엔드만 호출
- **백엔드**: 환경 변수에서 API 키 관리, 외부 API 호출
- **사용자**: API 키 걱정 없이 서비스 이용

### 3.2 백엔드 URL 업데이트
Streamlit Cloud의 **Secrets**에서:
```toml
BACKEND_URL = "https://your-username-travel-agent-ai-backend.hf.space"
```

### 3.2 CORS 설정 확인
백엔드에서 프론트엔드 도메인 허용:
```python
# travel_agent/backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-streamlit-app.streamlit.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🌍 **4단계: 도메인 설정 (선택사항)**

### 4.1 커스텀 도메인 구매
- Namecheap, GoDaddy 등에서 도메인 구매
- 예: `travelagent.ai`

### 4.2 DNS 설정
- **A Record**: Streamlit Cloud IP 주소
- **CNAME**: Hugging Face Spaces URL

### 4.3 SSL 인증서
- Streamlit Cloud: 자동 HTTPS 제공
- Hugging Face Spaces: 자동 HTTPS 제공

---

## ✅ **배포 완료 확인**

### 프론트엔드 테스트
1. Streamlit Cloud URL 접속
2. 여행 계획 생성 테스트
3. 백엔드 연결 확인

### 백엔드 테스트
1. Hugging Face Spaces URL 접속
2. API 문서 확인 (`/docs`)
3. 상태 확인 (`/api/status`)

---

## 🚨 **문제 해결**

### 일반적인 오류
- **Import 오류**: requirements.txt 확인
- **API 키 오류**: 환경 변수 재설정
- **CORS 오류**: allow_origins 설정 확인

### 로그 확인
- Streamlit Cloud: App logs
- Hugging Face Spaces: Build logs

---

## 📞 **지원**

문제가 발생하면:
1. 로그 확인
2. 환경 변수 재설정
3. GitHub Issues 등록

---

**🎉 배포 완료 후 Travel Agent AI를 전 세계에서 사용할 수 있습니다!**
