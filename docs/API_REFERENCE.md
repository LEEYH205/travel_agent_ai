# Travel Agent AI API 참조 문서

## 개요

Travel Agent AI는 AI 에이전트가 협력하여 맞춤형 여행 일정을 생성하는 시스템입니다. 이 문서는 백엔드 API의 사용법을 설명합니다.

## 기본 정보

- **Base URL**: `http://localhost:8000` (개발 환경)
- **API 버전**: v1.0.0
- **인증**: API 키 기반 (일부 엔드포인트)
- **응답 형식**: JSON

## 인증

대부분의 API 엔드포인트는 공개적으로 접근 가능하지만, CrewAI 모드를 사용하려면 OpenAI API 키가 필요합니다.

```bash
# 환경 변수 설정
export OPENAI_API_KEY="your-openai-api-key"
export OPENWEATHER_API_KEY="your-openweather-api-key"
export GOOGLE_MAPS_API_KEY="your-google-maps-api-key"
export FOURSQUARE_API_KEY="your-foursquare-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```

## 엔드포인트

### 1. 시스템 상태

#### 헬스 체크
```http
GET /health
```

**응답 예시:**
```json
{
  "status": "healthy",
  "service": "Travel Agent AI",
  "version": "1.0.0",
  "timestamp": 1704067200.0
}
```

#### API 상태 확인
```http
GET /api/status
```

**응답 예시:**
```json
{
  "api_keys": {
    "openai": true,
    "openweather": true,
    "google_maps": true,
    "foursquare": false,
    "tavily": true
  },
  "environment": "development",
  "features": {
    "crewai": true,
    "weather": true,
    "directions": true,
    "places": false,
    "web_search": true
  },
  "version": "1.0.0"
}
```

### 2. 여행 계획 생성

#### 여행 계획 생성 (메인)
```http
POST /plan
```

**요청 본문:**
```json
{
  "destination": "파리",
  "start_date": "2024-02-01",
  "end_date": "2024-02-04",
  "interests": ["역사", "예술", "음식"],
  "pace": "balanced",
  "budget_level": "mid",
  "party": 2,
  "locale": "ko_KR",
  "transport_mode": "walking",
  "include_weather": true
}
```

**쿼리 파라미터:**
- `mode`: 계획 생성 모드 (`graph` 또는 `crew`, 기본값: `crew`)
- `include_weather`: 날씨 정보 포함 여부 (기본값: `true`)
- `include_local_info`: 현지 정보 포함 여부 (기본값: `true`)

**응답 예시:**
```json
{
  "itinerary": {
    "summary": "파리 3박 4일 여행",
    "days": [
      {
        "date": "2024-02-01",
        "morning": [
          {
            "name": "에펠탑",
            "category": "landmark",
            "lat": 48.8584,
            "lon": 2.2945,
            "description": "파리의 상징적인 철탑",
            "est_stay_min": 120
          }
        ],
        "afternoon": [...],
        "evening": [...],
        "transfers": [...]
      }
    ],
    "tips": {
      "etiquette": ["현지 문화를 존중하세요"],
      "packing": ["편한 신발", "보조 배터리"],
      "safety": ["소매치기 주의"]
    }
  },
  "success": true,
  "message": "여행 계획이 성공적으로 생성되었습니다",
  "processing_time": 15.2,
  "mode": "crew"
}
```

### 3. 날씨 정보

#### 날씨 정보 조회
```http
GET /api/weather/{destination}?start_date={start_date}&end_date={end_date}
```

**응답 예시:**
```json
{
  "destination": "파리",
  "weather": [
    {
      "date": "2024-02-01",
      "temp_c": 15.0,
      "temp_f": 59.0,
      "condition": "clear",
      "humidity": 65,
      "wind_speed": 12.0,
      "summary": "맑음"
    }
  ]
}
```

### 4. 장소 검색

#### 장소 검색
```http
GET /api/places/{destination}?interests={interests}&limit={limit}
```

**쿼리 파라미터:**
- `interests`: 관심사 (쉼표로 구분)
- `limit`: 검색 결과 수 (1-50, 기본값: 10)

**응답 예시:**
```json
{
  "destination": "파리",
  "places": [
    {
      "name": "에펠탑",
      "category": "landmark",
      "lat": 48.8584,
      "lon": 2.2945,
      "description": "파리의 상징적인 철탑",
      "est_stay_min": 120,
      "rating": 4.5,
      "price_level": 3
    }
  ]
}
```

### 5. 현지 정보

#### 현지 정보 조회
```http
GET /api/local-info/{destination}?language={language}
```

**쿼리 파라미터:**
- `language`: 언어 코드 (기본값: `ko`)

**응답 예시:**
```json
{
  "destination": "파리",
  "local_info": {
    "title": "파리",
    "summary": "프랑스의 수도이자 예술과 문화의 도시",
    "cultural_info": {
      "language": "프랑스어",
      "currency": "유로"
    },
    "travel_tips": ["에펠탑 방문을 추천합니다"],
    "attractions": ["에펠탑", "루브르 박물관", "노트르담 대성당"]
  }
}
```

### 6. 피드백

#### 피드백 제출
```http
POST /api/feedback
```

**요청 본문:**
```json
{
  "overall_satisfaction": 4,
  "feedback_type": "schedule",
  "improvement_areas": ["하루에 너무 많은 장소를 방문합니다"],
  "free_feedback": "전반적으로 만족스럽습니다"
}
```

**응답 예시:**
```json
{
  "message": "피드백이 성공적으로 제출되었습니다",
  "feedback_id": "feedback_1704067200",
  "timestamp": 1704067200.0
}
```

### 7. 통계

#### 시스템 통계
```http
GET /api/stats
```

**응답 예시:**
```json
{
  "total_plans_generated": 150,
  "crewai_usage": 120,
  "graph_usage": 30,
  "popular_destinations": ["파리", "도쿄", "뉴욕"],
  "average_satisfaction": 4.2,
  "last_updated": 1704067200.0
}
```

## 에러 처리

### 에러 응답 형식
```json
{
  "error": true,
  "error_code": "VALIDATION_ERROR",
  "message": "여행지를 입력해주세요",
  "status_code": 400,
  "timestamp": "2024-01-01T12:00:00",
  "details": {
    "field": "destination"
  },
  "request_id": "req_12345"
}
```

### HTTP 상태 코드
- `200`: 성공
- `400`: 잘못된 요청 (검증 오류)
- `401`: 인증 실패
- `404`: 리소스를 찾을 수 없음
- `429`: 요청 제한 초과
- `500`: 서버 내부 오류

### 일반적인 에러 코드
- `VALIDATION_ERROR`: 데이터 검증 오류
- `API_KEY_ERROR`: API 키 관련 오류
- `EXTERNAL_API_ERROR`: 외부 API 호출 오류
- `RATE_LIMIT_ERROR`: API 호출 제한 오류
- `TIMEOUT_ERROR`: API 호출 시간 초과
- `RESOURCE_NOT_FOUND`: 리소스를 찾을 수 없음

## 사용 예시

### Python 클라이언트 예시
```python
import httpx
import asyncio

async def create_travel_plan():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/plan",
            json={
                "destination": "파리",
                "start_date": "2024-02-01",
                "end_date": "2024-02-04",
                "interests": ["역사", "예술"],
                "pace": "balanced",
                "budget_level": "mid",
                "party": 2
            }
        )
        return response.json()

# 사용
plan = asyncio.run(create_travel_plan())
print(plan)
```

### cURL 예시
```bash
# 여행 계획 생성
curl -X POST "http://localhost:8000/plan" \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "파리",
    "start_date": "2024-02-01",
    "end_date": "2024-02-04",
    "interests": ["역사", "예술"],
    "pace": "balanced",
    "budget_level": "mid",
    "party": 2
  }'

# 날씨 정보 조회
curl "http://localhost:8000/api/weather/파리?start_date=2024-02-01&end_date=2024-02-04"

# 장소 검색
curl "http://localhost:8000/api/places/파리?interests=역사,예술&limit=5"
```

## 제한 사항

- **여행 기간**: 최대 30일
- **관심사**: 최대 20개
- **여행 인원**: 최대 20명
- **API 호출 제한**: 분당 10회 (API), 분당 30회 (프론트엔드)

## 지원

문제가 발생하거나 질문이 있으시면 GitHub Issues를 통해 문의해주세요.

- **GitHub**: https://github.com/LEEYH205/travel_agent_ai
- **문서**: 이 README 파일
- **API 문서**: http://localhost:8000/docs (Swagger UI)
