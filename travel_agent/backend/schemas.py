from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import date, datetime

class UserPreferences(BaseModel):
    """사용자 여행 선호도"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "destination": "파리",
                "start_date": "2024-02-01",
                "end_date": "2024-02-03",
                "interests": ["역사", "예술"],
                "pace": "balanced",
                "budget_level": "mid",
                "party": 2
            }
        }
    )
    
    destination: str = Field(..., description="여행지", min_length=1, max_length=100)
    start_date: str = Field(..., description="시작일 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료일 (YYYY-MM-DD)")
    interests: List[str] = Field(..., description="관심사 목록", min_length=1, max_length=20)
    pace: str = Field("balanced", description="여행 페이스", pattern="^(relaxed|balanced|packed)$")
    budget_level: str = Field("mid", description="예산 수준", pattern="^(low|mid|high)$")
    party: int = Field(2, description="여행 인원", ge=1, le=20)
    locale: str = Field("ko_KR", description="언어 설정")
    transport_mode: str = Field("walking", description="주요 교통수단", pattern="^(walking|transit|driving)$")
    include_weather: bool = Field(True, description="날씨 정보 포함 여부")
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('날짜는 YYYY-MM-DD 형식이어야 합니다')
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        if 'start_date' in info.data:
            start = datetime.fromisoformat(info.data['start_date'])
            end = datetime.fromisoformat(v)
            if start >= end:
                raise ValueError('종료일은 시작일보다 늦어야 합니다')
        return v

class Place(BaseModel):
    """관광지 정보"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "에펠탑",
                "category": "landmark",
                "lat": 48.8584,
                "lon": 2.2945,
                "description": "파리의 상징적인 철탑",
                "est_stay_min": 120,
                "rating": 4.5,
                "price_level": 3
            }
        }
    )
    
    name: str = Field(..., description="장소명", min_length=1, max_length=200)
    category: str = Field("poi", description="카테고리")
    lat: float = Field(..., description="위도", ge=-90, le=90)
    lon: float = Field(..., description="경도", ge=-180, le=180)
    description: Optional[str] = Field(None, description="설명", max_length=1000)
    est_stay_min: int = Field(60, description="예상 체류시간(분)", ge=15, le=480)
    rating: Optional[float] = Field(None, description="평점", ge=0, le=5)
    price_level: Optional[int] = Field(None, description="가격 수준", ge=1, le=4)
    opening_hours: Optional[str] = Field(None, description="운영 시간")
    address: Optional[str] = Field(None, description="주소")
    website: Optional[str] = Field(None, description="웹사이트")
    phone: Optional[str] = Field(None, description="전화번호")

class Transfer(BaseModel):
    """이동 정보"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "from_place": "에펠탑",
                "to_place": "루브르 박물관",
                "travel_min": 25,
                "distance_km": 2.1,
                "mode": "walk"
            }
        }
    )
    
    from_place: str = Field(..., description="출발지")
    to_place: str = Field(..., description="도착지")
    travel_min: int = Field(..., description="이동 시간(분)", ge=1, le=300)
    distance_km: float = Field(..., description="거리(km)", ge=0, le=100)
    mode: str = Field("walk", description="교통수단", pattern="^(walk|transit|drive|bike)$")
    route_info: Optional[str] = Field(None, description="경로 정보")
    cost: Optional[float] = Field(None, description="비용")

class DayPlan(BaseModel):
    """일별 일정"""
    date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    morning: List[Place] = Field(default_factory=list, description="오전 일정")
    lunch: Optional[str] = Field(None, description="점심 장소 또는 추천")
    afternoon: List[Place] = Field(default_factory=list, description="오후 일정")
    dinner: Optional[str] = Field(None, description="저녁 장소 또는 추천")
    evening: List[Place] = Field(default_factory=list, description="저녁 일정")
    transfers: List[Transfer] = Field(default_factory=list, description="이동 정보")
    notes: Optional[str] = Field(None, description="특별 참고사항")
    
    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v):
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('날짜는 YYYY-MM-DD 형식이어야 합니다')

class Tips(BaseModel):
    """현지 가이드 팁"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "etiquette": ["현지 문화와 관습을 존중하세요"],
                "packing": ["편한 신발", "보조 배터리"],
                "safety": ["소매치기 주의", "늦은 밤 외진 골목 피하기"]
            }
        }
    )
    
    etiquette: List[str] = Field(default_factory=list, description="문화 및 예의", max_length=10)
    packing: List[str] = Field(default_factory=list, description="준비물", max_length=15)
    safety: List[str] = Field(default_factory=list, description="안전 및 주의사항", max_length=10)
    local_customs: Optional[List[str]] = Field(None, description="현지 관습", max_length=10)
    emergency_contacts: Optional[List[str]] = Field(None, description="긴급연락처", max_length=5)

class WeatherInfo(BaseModel):
    """날씨 정보"""
    date: str = Field(..., description="날짜")
    temp_c: float = Field(..., description="기온(섭씨)")
    temp_f: float = Field(..., description="기온(화씨)")
    condition: str = Field(..., description="날씨 상태")
    humidity: Optional[int] = Field(None, description="습도(%)")
    wind_speed: Optional[float] = Field(None, description="풍속(km/h)")
    precipitation: Optional[float] = Field(None, description="강수량(mm)")
    summary: Optional[str] = Field(None, description="날씨 요약")
    
    @field_validator('temp_f')
    @classmethod
    def calculate_fahrenheit(cls, v, info):
        if 'temp_c' in info.data:
            return round(info.data['temp_c'] * 9/5 + 32, 1)
        return v

class LocalInfo(BaseModel):
    """현지 정보"""
    title: str = Field(..., description="제목")
    summary: str = Field(..., description="요약")
    cultural_info: Optional[Dict[str, Any]] = Field(None, description="문화 정보")
    practical_info: Optional[Dict[str, Any]] = Field(None, description="실용 정보")
    travel_tips: Optional[List[str]] = Field(None, description="여행 팁")
    attractions: Optional[List[str]] = Field(None, description="주요 명소")
    events: Optional[List[str]] = Field(None, description="주요 이벤트")
    language: str = Field("ko", description="언어")

class Itinerary(BaseModel):
    """여행 일정"""
    summary: str = Field(..., description="일정 요약", max_length=500)
    days: List[DayPlan] = Field(..., description="일별 일정", min_length=1, max_length=30)
    tips: Tips = Field(..., description="현지 가이드 팁")
    weather_info: Optional[List[WeatherInfo]] = Field(None, description="날씨 정보")
    local_info: Optional[LocalInfo] = Field(None, description="현지 정보")
    total_distance: Optional[float] = Field(None, description="총 이동 거리(km)")
    total_cost: Optional[float] = Field(None, description="예상 총 비용")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    version: str = Field("1.0", description="일정 버전")

class PlanResponse(BaseModel):
    """여행 계획 응답"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "itinerary": {
                    "summary": "파리 3박 4일 여행",
                    "days": [],
                    "tips": {
                        "etiquette": ["현지 문화와 관습을 존중하세요"],
                        "packing": ["편한 신발", "보조 배터리"],
                        "safety": ["소매치기 주의"]
                    }
                },
                "success": True,
                "message": "여행 계획이 성공적으로 생성되었습니다",
                "mode": "crew",
                "processing_time": 15.2
            }
        }
    )
    
    itinerary: Itinerary = Field(..., description="여행 일정")
    success: bool = Field(True, description="성공 여부")
    message: str = Field("여행 계획이 성공적으로 생성되었습니다", description="응답 메시지")
    processing_time: Optional[float] = Field(None, description="처리 시간(초)")
    mode: str = Field(..., description="사용된 계획 생성 모드")
    local_info: Optional[Dict[str, Any]] = Field(None, description="현지 정보")
    api_usage: Optional[Dict[str, int]] = Field(None, description="API 사용량")

class ErrorResponse(BaseModel):
    """에러 응답"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": True,
                "message": "여행지를 입력해주세요",
                "status_code": 400,
                "timestamp": "2024-01-01T12:00:00",
                "details": {"field": "destination"},
                "request_id": "req_12345"
            }
        }
    )
    
    error: bool = Field(True, description="에러 발생 여부")
    message: str = Field(..., description="에러 메시지")
    status_code: int = Field(..., description="HTTP 상태 코드")
    timestamp: datetime = Field(default_factory=datetime.now, description="에러 발생 시간")
    details: Optional[Dict[str, Any]] = Field(None, description="상세 에러 정보")
    request_id: Optional[str] = Field(None, description="요청 ID")

class FeedbackData(BaseModel):
    """피드백 데이터"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_satisfaction": 4,
                "feedback_type": "schedule",
                "improvement_areas": ["하루에 너무 많은 장소를 방문합니다"],
                "free_feedback": "전반적으로 만족스럽습니다"
            }
        }
    )
    
    overall_satisfaction: int = Field(..., description="전체 만족도", ge=1, le=5)
    feedback_type: str = Field(..., description="피드백 유형")
    improvement_areas: Optional[List[str]] = Field(None, description="개선 영역")
    free_feedback: Optional[str] = Field(None, description="자유 의견")
    day_feedback: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="일별 피드백")
    place_feedback: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="장소별 피드백")
    improvement_request: Optional[str] = Field(None, description="개선 요청")
    additional_options: Optional[Dict[str, bool]] = Field(None, description="추가 옵션")
    contact_info: Optional[Dict[str, str]] = Field(None, description="연락처 정보")

class APIStatus(BaseModel):
    """API 상태 정보"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "api_keys": {
                    "openai": True,
                    "openweather": True,
                    "google_maps": True,
                    "foursquare": False,
                    "tavily": True
                },
                "environment": "development",
                "features": {
                    "crewai": True,
                    "weather": True,
                    "directions": True,
                    "places": False,
                    "web_search": True
                },
                "version": "1.0.0"
            }
        }
    )
    
    api_keys: Dict[str, bool] = Field(..., description="API 키 상태")
    environment: str = Field(..., description="환경")
    features: Dict[str, bool] = Field(..., description="기능별 사용 가능 여부")
    uptime: Optional[float] = Field(None, description="가동 시간(초)")
    version: str = Field("1.0.0", description="API 버전")

class Statistics(BaseModel):
    """시스템 통계"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_plans_generated": 150,
                "crewai_usage": 120,
                "graph_usage": 30,
                "popular_destinations": ["파리", "도쿄", "뉴욕"],
                "average_satisfaction": 4.2,
                "last_updated": 1704067200.0
            }
        }
    )
    
    total_plans_generated: int = Field(0, description="총 생성된 계획 수")
    crewai_usage: int = Field(0, description="CrewAI 모드 사용 횟수")
    graph_usage: int = Field(0, description="Graph 모드 사용 횟수")
    popular_destinations: List[str] = Field(default_factory=list, description="인기 여행지")
    average_satisfaction: float = Field(0.0, description="평균 만족도", ge=0, le=5)
    last_updated: float = Field(..., description="마지막 업데이트 시간")
