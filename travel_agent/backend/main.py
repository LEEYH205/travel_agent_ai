from __future__ import annotations
import logging
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
import os

from travel_agent.backend.schemas import UserPreferences, PlanResponse, ErrorResponse
from travel_agent.backend.graph import plan_itinerary
from travel_agent.backend.orchestrators.crew import plan_with_crew
from travel_agent.backend.tools.weather import get_forecast_weather
from travel_agent.backend.tools.places import search_places_async
from travel_agent.backend.tools.wiki import get_destination_info

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('travel_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 애플리케이션 생명주기 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행
    logger.info("🚀 Travel Agent AI 백엔드 서버 시작")
    logger.info(f"환경: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"OpenAI API 키: {'설정됨' if os.getenv('OPENAI_API_KEY') else '미설정'}")
    logger.info(f"OpenWeather API 키: {'설정됨' if os.getenv('OPENWEATHER_API_KEY') else '미설정'}")
    logger.info(f"Google Maps API 키: {'설정됨' if os.getenv('GOOGLE_MAPS_API_KEY') else '미설정'}")
    logger.info(f"FourSquare API 키: {'설정됨' if os.getenv('FOURSQUARE_API_KEY') else '미설정'}")
    
    yield
    
    # 종료 시 실행
    logger.info("🛑 Travel Agent AI 백엔드 서버 종료")

# FastAPI 앱 생성
app = FastAPI(
    title="AI 여행 계획사 - Travel Agent AI",
    description="AI 에이전트가 협력하여 맞춤형 여행 일정을 생성하는 시스템",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 미들웨어 설정
# CORS 설정 - 개발/프로덕션 환경에 따라 다르게 설정
cors_origins = [
    "http://localhost:8501",  # 로컬 개발
    "http://localhost:3000",  # React 개발 (향후)
    "https://*.streamlit.app",  # Streamlit Cloud
    "https://*.hf.space",      # Hugging Face Spaces
]

# 환경 변수에서 추가 도메인 허용
additional_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
if additional_origins and additional_origins[0]:
    cors_origins.extend([origin.strip() for origin in additional_origins])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # 요청 정보 로깅
    logger.info(f"📥 {request.method} {request.url.path} - {request.client.host if request.client else 'unknown'}")
    
    response = await call_next(request)
    
    # 응답 시간 계산
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # 응답 정보 로깅
    logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response

# 의존성 함수들
async def get_api_keys() -> Dict[str, bool]:
    """API 키 상태 확인"""
    return {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "openweather": bool(os.getenv("OPENWEATHER_API_KEY")),
        "google_maps": bool(os.getenv("GOOGLE_MAPS_API_KEY")),
        "foursquare": bool(os.getenv("FOURSQUARE_API_KEY")),
        "tavily": bool(os.getenv("TAVILY_API_KEY"))
    }

async def validate_preferences(pref: UserPreferences) -> UserPreferences:
    """사용자 선호도 검증"""
    # 기본 검증
    if not pref.destination or len(pref.destination.strip()) == 0:
        raise HTTPException(status_code=400, detail="여행지를 입력해주세요")
    
    if not pref.interests or len(pref.interests) == 0:
        raise HTTPException(status_code=400, detail="관심사를 하나 이상 선택해주세요")
    
    # 날짜 검증
    from datetime import datetime
    try:
        start_date = datetime.fromisoformat(pref.start_date)
        end_date = datetime.fromisoformat(pref.end_date)
        
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="종료일은 시작일보다 늦어야 합니다")
        
        # 여행 기간 제한 (최대 30일)
        if (end_date - start_date).days > 30:
            raise HTTPException(status_code=400, detail="여행 기간은 최대 30일까지 가능합니다")
            
    except ValueError:
        raise HTTPException(status_code=400, detail="올바른 날짜 형식을 입력해주세요")
    
    return pref

async def validate_api_keys_for_mode(mode: str) -> None:
    """모드별 필수 API 키 검증"""
    if mode == "crew":
        # CrewAI 모드에서는 OpenAI API 키가 필수
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=400, 
                detail="CrewAI 모드를 사용하려면 OpenAI API 키가 필요합니다. 백엔드 관리자에게 문의하세요."
            )
    
    # 다른 모드들에 대한 검증도 추가 가능
    return None

# 헬스 체크 엔드포인트
@app.get("/health", tags=["시스템"])
async def health_check():
    """시스템 상태 확인"""
    return {
        "status": "healthy",
        "service": "Travel Agent AI",
        "version": "1.0.0",
        "timestamp": time.time()
    }

# API 키 상태 확인 엔드포인트
@app.get("/api/status", tags=["시스템"])
async def api_status(api_keys: Dict[str, bool] = Depends(get_api_keys)):
    """API 키 상태 및 시스템 정보"""
    return {
        "api_keys": api_keys,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "features": {
            "crewai": api_keys["openai"],
            "weather": api_keys["openweather"],
            "directions": api_keys["google_maps"],
            "places": api_keys["foursquare"],
            "web_search": api_keys["tavily"]
        },
        "version": "1.0.0",
        "uptime": None  # TODO: 서버 시작 시간을 추적하여 실제 uptime 계산
    }

# 여행 계획 생성 메인 엔드포인트
@app.post("/plan", response_model=PlanResponse, tags=["여행 계획"])
async def create_travel_plan(
    pref: UserPreferences = Depends(validate_preferences),
    mode: str = Query("crew", enum=["graph", "crew"], description="계획 생성 모드"),
    include_weather: bool = Query(True, description="날씨 정보 포함 여부"),
    include_local_info: bool = Query(True, description="현지 정보 포함 여부")
):
    """
    AI 에이전트 기반 맞춤형 여행 계획 생성
    
    - **graph**: 기본 알고리즘 기반 계획 생성
    - **crew**: CrewAI 에이전트 협업 기반 계획 생성 (OpenAI API 필요)
    """
    try:
        logger.info(f"🎯 여행 계획 생성 시작: {pref.destination} ({pref.start_date} ~ {pref.end_date})")
        logger.info(f"모드: {mode}, 관심사: {pref.interests}")
        
        start_time = time.time()
        
        # API 키 검증
        await validate_api_keys_for_mode(mode)
        
        # 모드별 계획 생성
        if mode == "crew":
            # CrewAI 모드
            result = await plan_with_crew(pref)
            logger.info("🤖 CrewAI 모드로 계획 생성 완료")
            
        else:
            # Graph 모드
            result = await plan_itinerary(pref)
            logger.info("📊 Graph 모드로 계획 생성 완료")
        
        # 추가 정보 수집 (선택사항)
        if include_weather:
            try:
                weather_data = await get_forecast_weather(pref.destination, pref.start_date, pref.end_date)
                if weather_data:
                    # 날씨 정보를 결과에 추가
                    result.weather_info = weather_data
                    logger.info("🌤️ 날씨 정보 추가 완료")
            except Exception as e:
                logger.warning(f"날씨 정보 수집 실패: {e}")
        
        if include_local_info:
            try:
                local_info = await get_destination_info(pref.destination, "ko")
                if local_info:
                    # 현지 정보를 결과에 추가
                    result.local_info = local_info
                    logger.info("🏛️ 현지 정보 추가 완료")
            except Exception as e:
                logger.warning(f"현지 정보 수집 실패: {e}")
        
        process_time = time.time() - start_time
        logger.info(f"✅ 여행 계획 생성 완료: {process_time:.3f}초")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"여행 계획 생성 중 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"여행 계획 생성 중 오류가 발생했습니다: {str(e)}"
        )

# 날씨 정보 조회 엔드포인트
@app.get("/api/weather/{destination}", tags=["날씨"])
async def get_weather_info(
    destination: str,
    start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")
):
    """여행 기간의 날씨 정보 조회"""
    try:
        weather_data = await get_forecast_weather(destination, start_date, end_date)
        return {"destination": destination, "weather": weather_data}
    except Exception as e:
        logger.error(f"날씨 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="날씨 정보를 가져올 수 없습니다")

# 장소 검색 엔드포인트
@app.get("/api/places/{destination}", tags=["장소"])
async def search_places(
    destination: str,
    interests: str = Query(..., description="관심사 (쉼표로 구분)"),
    limit: int = Query(10, ge=1, le=50, description="검색 결과 수")
):
    """목적지의 관심사별 장소 검색"""
    try:
        interests_list = [interest.strip() for interest in interests.split(",")]
        places = await search_places_async(destination, interests_list, limit)
        return {"destination": destination, "places": places}
    except Exception as e:
        logger.error(f"장소 검색 실패: {e}")
        raise HTTPException(status_code=500, detail="장소 검색에 실패했습니다")

# 현지 정보 조회 엔드포인트
@app.get("/api/local-info/{destination}", tags=["현지 정보"])
async def get_local_information(
    destination: str,
    language: str = Query("ko", description="언어 코드")
):
    """목적지의 현지 정보 조회"""
    try:
        local_info = await get_destination_info(destination, language)
        return {"destination": destination, "local_info": local_info}
    except Exception as e:
        logger.error(f"현지 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="현지 정보를 가져올 수 없습니다")

# 피드백 수집 엔드포인트
@app.post("/api/feedback", tags=["피드백"])
async def submit_feedback(feedback_data: Dict[str, Any]):
    """사용자 피드백 수집"""
    try:
        logger.info(f"📝 피드백 수신: {feedback_data.get('feedback_type', 'unknown')}")
        
        # 피드백 데이터 검증
        required_fields = ["overall_satisfaction", "feedback_type"]
        for field in required_fields:
            if field not in feedback_data:
                raise HTTPException(status_code=400, detail=f"필수 필드 누락: {field}")
        
        # 피드백 저장 (실제 구현에서는 데이터베이스에 저장)
        feedback_id = f"feedback_{int(time.time())}"
        
        logger.info(f"✅ 피드백 저장 완료: {feedback_id}")
        
        return {
            "message": "피드백이 성공적으로 제출되었습니다",
            "feedback_id": feedback_id,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"피드백 처리 실패: {e}")
        raise HTTPException(status_code=500, detail="피드백 처리에 실패했습니다")

# 통계 정보 엔드포인트
@app.get("/api/stats", tags=["통계"])
async def get_statistics():
    """시스템 사용 통계"""
    # 실제 구현에서는 데이터베이스에서 통계 수집
    return {
        "total_plans_generated": 0,
        "crewai_usage": 0,
        "graph_usage": 0,
        "popular_destinations": [],
        "average_satisfaction": 0.0,
        "last_updated": time.time()
    }

# 에러 핸들러
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 처리"""
    logger.warning(f"HTTP 예외 발생: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(ErrorResponse(
            error=True,
            message=exc.detail,
            status_code=exc.status_code
        ))
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    logger.error(f"예상치 못한 오류 발생: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=jsonable_encoder(ErrorResponse(
            error=True,
            message="서버 내부 오류가 발생했습니다",
            status_code=500
        ))
    )

# 메인 실행
if __name__ == "__main__":
    uvicorn.run(
        "travel_agent.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
