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

### **Phase 2: 백엔드 핵심 기능 구현** 🔄
- [x] 2.1 Agent 시스템 구축
  - [x] 2.1.1 ResearchAgent (정보 수집) - CrewAI 기반으로 개선 완료
  - [x] 2.1.2 AttractionsAgent (명소 추천) - CrewAI 기반으로 개선 완료
  - [x] 2.1.3 ItineraryPlannerAgent (일정 계획) - CrewAI 기반으로 개선 완료
  - [x] 2.1.4 LocalGuideAgent (현지 정보) - 기본 구조 완성
  - [x] 2.1.5 CriticAgent (품질 검토) - 구조 설계 완료
- [ ] 2.2 외부 API 연동 도구 구현
  - [ ] 2.2.1 날씨 API (OpenWeather)
  - [ ] 2.2.2 장소 검색 API (FourSquare/Google Places)
  - [ ] 2.2.3 경로 계산 API (Google Maps/Bing Maps)
  - [ ] 2.2.4 위키백과 API
- [ ] 2.3 CrewAI Orchestrator 구현

### **Phase 3: 프론트엔드 UI/UX 구현** ⏳
- [ ] 3.1 사용자 입력 폼 (여행지, 기간, 선호사항)
- [ ] 3.2 일정 결과 표시 (테이블/카드 형태)
- [ ] 3.3 대화형 피드백 시스템
- [ ] 3.4 반응형 디자인

### **Phase 4: 통합 및 최적화** ⏳
- [ ] 4.1 백엔드-프론트엔드 연동
- [ ] 4.2 에러 처리 및 예외 상황 관리
- [ ] 4.3 성능 최적화
- [ ] 4.4 테스트 코드 작성

### **Phase 5: 배포 및 문서화** ⏳
- [ ] 5.1 클라우드 배포 (Streamlit Cloud/Hugging Face)
- [ ] 5.2 API 문서화
- [ ] 5.3 사용자 가이드 작성

## 🚀 현재 진행 상황

**현재 단계**: Phase 2.1 - Agent 시스템 구축 완료
**다음 단계**: Phase 2.2 - 외부 API 연동 도구 구현

### 완료된 작업
- ✅ CrewAI 기반 Agent 클래스 구조 설계
- ✅ ResearchAgent: 여행지 정보 수집 및 시즌별 분석
- ✅ AttractionsAgent: 사용자 선호도 기반 명소 선별
- ✅ ItineraryPlannerAgent: 지능적인 일정 계획 및 경로 최적화
- ✅ LocalGuideAgent: 현지 문화 및 팁 제공
- ✅ CriticAgent: 일정 품질 검토 및 개선 제안

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

# 2) Run backend
uvicorn travel_agent.backend.main:app --reload --port 8000

# 3) Run UI (new terminal)
streamlit run travel_agent/frontend/app.py
```

## 🔑 Environment variables (.env)

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

## 🔄 다음 단계

1. **외부 API 연동 도구 구현** (Phase 2.2)
   - OpenWeather API 연동
   - FourSquare/Google Places API 연동
   - Google Maps Directions API 연동
   - Wikipedia API 연동

2. **CrewAI Orchestrator 구현** (Phase 2.3)
   - Agent 간 협업 워크플로우 설계
   - 작업 분배 및 결과 통합

3. **프론트엔드 UI 개선** (Phase 3)
   - 사용자 입력 폼 개선
   - 일정 결과 시각화
   - 대화형 피드백 시스템

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.
