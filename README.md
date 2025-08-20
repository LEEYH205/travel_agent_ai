# Agent Travel Planner (MVP)

AI 에이전트가 협력하여 사용자 맞춤형 여행 일정을 생성하는 시스템입니다.

## 🎯 프로젝트 개요

이 시스템은 단일 모델이 아닌 복수의 **에이전트(Agent)**가 협력하여 여행 정보를 찾아주고 세부 일정을 세우는 것이 특징입니다.

### 주요 기능
- **여행지 정보 수집**: 목적지의 최신 정보, 날씨, 시즌별 특이사항 수집
- **관광지 추천**: 사용자 관심사와 선호도에 맞는 맞춤형 명소 추천
- **일정 최적화**: 여행 스타일과 제약 조건을 고려한 최적 일정 계획
- **현지 팁 제공**: 현지 문화, 주의사항, 추천 준비물 안내
- **대화형 개선**: 사용자 피드백을 통한 실시간 일정 조정

## 📋 프로젝트 WBS (Work Breakdown Structure)

### **Phase 1: 프로젝트 기반 설정 및 환경 구성** ✅
- [x] 1.1 프로젝트 구조 설계
- [x] 1.2 기본 의존성 설치
- [x] 1.3 환경 변수 설정
- [x] 1.4 Git 저장소 초기화

### **Phase 2: 백엔드 핵심 기능 구현** ✅
- [x] 2.1 Agent 시스템 구축
  - [x] 2.1.1 ResearchAgent (정보 수집) - CrewAI 기반으로 완성
  - [x] 2.1.2 AttractionsAgent (명소 추천) - CrewAI 기반으로 완성
  - [x] 2.1.3 ItineraryPlannerAgent (일정 계획) - CrewAI 기반으로 완성
  - [x] 2.1.4 LocalGuideAgent (현지 정보) - CrewAI 기반으로 완성
  - [x] 2.1.5 CriticAgent (품질 검토) - CrewAI 기반으로 완성
- [x] 2.2 외부 API 연동 도구 구현
  - [x] 2.2.1 날씨 API (OpenWeather) - 완성
  - [x] 2.2.2 장소 검색 API (FourSquare) - 완성 (데모 데이터 포함)
  - [x] 2.2.3 경로 계산 API (Google Maps) - 완성
  - [x] 2.2.4 위키백과 API - 완성
  - [x] 2.2.5 웹 검색 API (Tavily) - 완성
- [x] 2.3 CrewAI Orchestrator 구현 - 완성

### **Phase 3: 프론트엔드 UI/UX 구현** ✅
- [x] 3.1 사용자 입력 폼 (여행지, 기간, 선호사항) - Streamlit 기반 완성
- [x] 3.2 일정 결과 표시 (테이블/카드 형태) - 완성
- [x] 3.3 대화형 피드백 시스템 - 완성
- [x] 3.4 반응형 디자인 - 완성

### **Phase 4: 통합 및 최적화** ✅
- [x] 4.1 백엔드-프론트엔드 연동 - 완성
- [x] 4.2 에러 처리 및 예외 상황 관리 - 완성
- [x] 4.3 성능 최적화 - 캐싱 및 폴백 시스템 완성
- [x] 4.4 테스트 코드 작성 - 19개 테스트 모두 통과

### **Phase 5: 배포 및 문서화** ✅
- [x] 5.1 클라우드 배포 준비 - Docker 및 Docker Compose 완성
- [x] 5.2 API 문서화 - FastAPI 자동 문서화 완성
- [x] 5.3 사용자 가이드 작성 - README 및 TODO 완성
- [x] 5.4 백엔드 오류 수정 완료 (local_info 필드, 날씨 타입 오류)
- [x] 5.5 실제 클라우드 배포 완료 (Streamlit Cloud + Hugging Face Spaces)

## 🚀 현재 진행 상황

**현재 단계**: Phase 5.5 완료 - 클라우드 배포 완료 ✅
**다음 단계**: Phase 6 - 성능 모니터링 및 최적화

### 완료된 작업
- ✅ CrewAI 기반 Agent 시스템 완성 (5개 에이전트)
- ✅ 외부 API 연동 도구 완성 (날씨, 장소, 경로, 위키, 웹검색)
- ✅ CrewAI Orchestrator 완성 및 최적화
- ✅ Streamlit 프론트엔드 완성 (사용자 입력, 결과 표시, 피드백)
- ✅ 백엔드-프론트엔드 통합 완성
- ✅ 에러 처리 및 폴백 시스템 완성
- ✅ 테스트 스위트 완성 (19개 테스트 모두 통과)
- ✅ Docker 배포 환경 구축 완성
- ✅ 백엔드 오류 수정 완료 (local_info 필드, 날씨 타입 오류)
- ✅ 클라우드 배포 완료 (Streamlit Cloud + Hugging Face Spaces)

## 🛠️ 기술 스택

- **백엔드**: Python, FastAPI, CrewAI, LangChain
- **프론트엔드**: Streamlit, React (예정)
- **AI/LLM**: OpenAI GPT-4, CrewAI Framework
- **외부 API**: OpenWeather, FourSquare, Google Maps, Wikipedia
- **데이터베이스**: SQLite (개발), PostgreSQL (운영 예정)

## 📁 프로젝트 구조

```
travel_agent/
├── backend/
│   ├── agents/           # AI 에이전트들
│   │   ├── researcher.py      # 여행지 정보 수집
│   │   ├── attractions.py     # 명소 추천
│   │   ├── planner.py         # 일정 계획
│   │   ├── local_guide.py     # 현지 정보
│   │   └── critic.py          # 품질 검토
│   ├── tools/            # 외부 API 연동 도구
│   ├── orchestrators/    # Agent 조율
│   └── schemas.py        # 데이터 모델
├── frontend/             # 사용자 인터페이스
└── tests/                # 테스트 코드
```

## 🚀 Quick Start

```bash
# 1) Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your keys if available

# 2) Run Backend (Terminal 1)
source .venv/bin/activate
python -m uvicorn travel_agent.backend.main:app --reload --port 8002

# 3) Run Frontend (Terminal 2)
source .venv/bin/activate
streamlit run travel_agent/frontend/app.py --server.port 8501
```

### 🌐 **접속 정보**
- **프론트엔드**: http://localhost:8501
- **백엔드 API**: http://localhost:8002
- **API 문서**: http://localhost:8002/docs

### ⚠️ **중요 사항**
- **백엔드**: 프로젝트 루트에서 실행해야 함 (import 문제 해결)
- **포트 충돌**: 8000, 8001이 사용 중인 경우 다른 포트 사용
- **가상환경**: 반드시 `.venv` 활성화 후 실행

## 🖥️ **상세 실행 방법**

### **백엔드 실행 (Terminal 1)**
```bash
# 프로젝트 루트에서
cd /path/to/travel_agent
source .venv/bin/activate
python -m uvicorn travel_agent.backend.main:app --reload --port 8002
```

### **프론트엔드 실행 (Terminal 2)**
```bash
# 새 터미널에서 (프로젝트 루트)
cd /path/to/travel_agent
source .venv/bin/activate
streamlit run travel_agent/frontend/app.py --server.port 8501
```

### **포트 변경이 필요한 경우**
```bash
# 백엔드 포트 변경
python -m uvicorn travel_agent.backend.main:app --reload --port 8003

# 프론트엔드 포트 변경
streamlit run travel_agent/frontend/app.py --server.port 8502
```

### **문제 해결**
- **Import 오류**: 프로젝트 루트에서 실행 확인
- **포트 충돌**: `lsof -i :8002`로 포트 사용 확인
- **가상환경**: `which python`으로 올바른 Python 경로 확인

## 🌐 **클라우드 배포 정보**

### **Streamlit Cloud (프론트엔드)**
- **URL**: https://travelagentai-lyh205.streamlit.app/
- **상태**: ✅ 배포 완료
- **백엔드 연결**: Hugging Face Spaces 백엔드와 연동
- **환경 변수**: Streamlit Cloud Secrets에서 관리

### **Hugging Face Spaces (백엔드)**
- **URL**: https://eddieleeyh-travel-agent-ai-backend.hf.space/
- **상태**: ✅ 배포 완료
- **API 엔드포인트**: 
  - 루트: `/` - API 정보 및 상태
  - 문서: `/docs` - FastAPI 자동 문서화
  - 헬스: `/health` - 시스템 상태 확인
  - 상태: `/api/status` - API 키 상태 확인
  - 계획: `/plan` - 여행 계획 생성
- **환경 변수**: Hugging Face Space Secrets에서 관리

### **연동 구조**
```
Streamlit Cloud (프론트엔드) 
    ↓ HTTP API 호출
Hugging Face Spaces (백엔드)
    ↓ OpenAI API 호출
OpenAI GPT-4 (AI 모델)
```

---

## 🔑 **Environment variables (.env)**

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
TAVILY_API_KEY=

OPENWEATHER_API_KEY=
FOURSQUARE_API_KEY=
GOOGLE_MAPS_API_KEY=
BING_MAPS_KEY=

APP_ENV=dev
DEFAULT_LOCALE=ko_KR
```

## 📝 Notes

- **Graph mode**: Mock places + heuristic routing (Haversine) - 외부 LLM 불필요
- **Crew mode**: CrewAI를 통한 Researcher/Attractions/Planner/LocalGuide 협업
- **Production**: `tools/places.py`와 `tools/directions.py`를 실제 API로 교체 필요

## 🔄 **다음 단계**

### **Phase 6: 성능 모니터링 및 최적화** 🔄
1. **성능 모니터링 구축**
   - Prometheus + Grafana 모니터링 시스템
   - API 응답 시간 및 사용량 추적
   - Hugging Face Space 리소스 모니터링

2. **성능 최적화**
   - API 응답 시간 최적화
   - 캐싱 전략 개선
   - 사용자 피드백 분석 시스템

### **Phase 7: 추가 기능 개발** 📋
1. **사용자 경험 개선**
   - 다국어 지원 (영어, 일본어 등)
   - 모바일 반응형 UI 개선
   - 소셜 기능 (여행 계획 공유)

2. **고급 기능**
   - 실시간 여행 계획 수정
   - AI 기반 여행 패턴 분석
   - 개인화된 추천 시스템

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.
