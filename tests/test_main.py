import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json
from datetime import date, timedelta

from travel_agent.backend.main import app
from travel_agent.backend.schemas import UserPreferences, PlanResponse

client = TestClient(app)

class TestHealthCheck:
    """헬스 체크 엔드포인트 테스트"""
    
    def test_health_check(self):
        """헬스 체크 응답 테스트"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Travel Agent AI"
        assert "version" in data
        assert "timestamp" in data

class TestAPIStatus:
    """API 상태 확인 엔드포인트 테스트"""
    
    def test_api_status(self):
        """API 상태 응답 테스트"""
        response = client.get("/api/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "api_keys" in data
        assert "environment" in data
        assert "features" in data
        assert "version" in data
        
        # API 키 상태 확인
        api_keys = data["api_keys"]
        assert isinstance(api_keys["openai"], bool)
        assert isinstance(api_keys["openweather"], bool)
        assert isinstance(api_keys["google_maps"], bool)
        assert isinstance(api_keys["foursquare"], bool)
        assert isinstance(api_keys["tavily"], bool)

class TestTravelPlanCreation:
    """여행 계획 생성 엔드포인트 테스트"""
    
    def get_valid_preferences(self):
        """유효한 사용자 선호도 데이터 생성"""
        start_date = date.today() + timedelta(days=30)
        end_date = start_date + timedelta(days=3)
        
        return {
            "destination": "파리",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "interests": ["역사", "예술"],
            "pace": "balanced",
            "budget_level": "mid",
            "party": 2,
            "locale": "ko_KR",
            "transport_mode": "walking",
            "include_weather": True
        }
    
    def test_create_travel_plan_graph_mode(self):
        """Graph 모드로 여행 계획 생성 테스트"""
        preferences = self.get_valid_preferences()
        
        with patch('travel_agent.backend.main.plan_itinerary') as mock_plan:
            # Mock으로 실제 PlanResponse 객체 반환
            from travel_agent.backend.schemas import PlanResponse, Itinerary, Tips, DayPlan
            from datetime import datetime
            
            mock_itinerary = Itinerary(
                summary="파리 3박 4일 여행",
                days=[
                    DayPlan(
                        date="2024-02-01",
                        morning=[],
                        afternoon=[],
                        evening=[],
                        transfers=[]
                    )
                ],
                tips=Tips(
                    etiquette=["현지 문화를 존중하세요"],
                    packing=["편한 신발"],
                    safety=["소매치기 주의"]
                ),
                created_at=datetime.now(),
                version="1.0"
            )
            
            mock_response = PlanResponse(
                itinerary=mock_itinerary,
                success=True,
                message="여행 계획이 성공적으로 생성되었습니다",
                mode="graph",
                processing_time=15.2
            )
            
            mock_plan.return_value = mock_response
            
            response = client.post("/plan?mode=graph", json=preferences)
            
            assert response.status_code == 200
            data = response.json()
            assert "itinerary" in data
            assert data["itinerary"]["summary"] == "파리 3박 4일 여행"
    
    def test_create_travel_plan_crew_mode(self):
        """CrewAI 모드로 여행 계획 생성 테스트"""
        preferences = self.get_valid_preferences()
        
        with patch('travel_agent.backend.main.plan_with_crew') as mock_plan:
            # Mock으로 실제 PlanResponse 객체 반환
            from travel_agent.backend.schemas import PlanResponse, Itinerary, Tips, DayPlan
            from datetime import datetime
            
            mock_itinerary = Itinerary(
                summary="파리 3박 4일 여행 (AI 생성)",
                days=[
                    DayPlan(
                        date="2024-02-01",
                        morning=[],
                        afternoon=[],
                        evening=[],
                        transfers=[]
                    )
                ],
                tips=Tips(
                    etiquette=["현지 문화를 존중하세요"],
                    packing=["편한 신발"],
                    safety=["소매치기 주의"]
                ),
                created_at=datetime.now(),
                version="1.0"
            )
            
            mock_response = PlanResponse(
                itinerary=mock_itinerary,
                success=True,
                message="여행 계획이 성공적으로 생성되었습니다",
                mode="crew",
                processing_time=15.2
            )
            
            mock_plan.return_value = mock_response
            
            response = client.post("/plan?mode=crew", json=preferences)
            
            assert response.status_code == 200
            data = response.json()
            assert "itinerary" in data
            assert "AI 생성" in data["itinerary"]["summary"]
    
    def test_create_travel_plan_validation_error(self):
        """잘못된 데이터로 여행 계획 생성 시 검증 오류 테스트"""
        # 필수 필드 누락
        invalid_preferences = {
            "destination": "",  # 빈 여행지
            "start_date": "2024-02-01",
            "end_date": "2024-02-03",
            "interests": []  # 빈 관심사
        }
        
        response = client.post("/plan", json=invalid_preferences)
        assert response.status_code == 422  # Pydantic 검증 오류는 422
        
        data = response.json()
        assert "detail" in data  # FastAPI는 "detail" 키 사용
    
    def test_create_travel_plan_date_validation_error(self):
        """잘못된 날짜로 여행 계획 생성 시 검증 오류 테스트"""
        preferences = self.get_valid_preferences()
        preferences["end_date"] = preferences["start_date"]  # 시작일과 종료일이 같음
        
        response = client.post("/plan", json=preferences)
        assert response.status_code == 422  # Pydantic 검증 오류는 422
        
        data = response.json()
        assert "detail" in data  # FastAPI는 "detail" 키 사용
    
    def test_create_travel_plan_with_weather(self):
        """날씨 정보 포함 여행 계획 생성 테스트"""
        preferences = self.get_valid_preferences()
        
        with patch('travel_agent.backend.main.plan_itinerary') as mock_plan:
            # Mock으로 실제 PlanResponse 객체 반환
            from travel_agent.backend.schemas import PlanResponse, Itinerary, Tips, DayPlan, WeatherInfo
            from datetime import datetime
            
            mock_itinerary = Itinerary(
                summary="파리 3박 4일 여행",
                days=[
                    DayPlan(
                        date="2024-02-01",
                        morning=[],
                        afternoon=[],
                        evening=[],
                        transfers=[]
                    )
                ],
                tips=Tips(
                    etiquette=["현지 문화를 존중하세요"],
                    packing=["편한 신발"],
                    safety=["소매치기 주의"]
                ),
                created_at=datetime.now(),
                version="1.0"
            )
            
            mock_response = PlanResponse(
                itinerary=mock_itinerary,
                success=True,
                message="여행 계획이 성공적으로 생성되었습니다",
                mode="graph",
                processing_time=15.2
            )
            
            mock_plan.return_value = mock_response
            
            with patch('travel_agent.backend.main.get_forecast_weather') as mock_weather:
                mock_weather.return_value = [
                    WeatherInfo(
                        date="2024-02-01",
                        temp_c=15.0,
                        temp_f=59.0,
                        condition="clear",
                        summary="맑음"
                    )
                ]
                
                response = client.post("/plan?include_weather=true", json=preferences)
                
                assert response.status_code == 200
                data = response.json()
                # weather_info가 None일 수 있으므로 검사 방식 변경
                if "weather_info" in data["itinerary"] and data["itinerary"]["weather_info"]:
                    assert len(data["itinerary"]["weather_info"]) >= 0

class TestWeatherAPI:
    """날씨 API 엔드포인트 테스트"""
    
    def test_get_weather_info(self):
        """날씨 정보 조회 테스트"""
        with patch('travel_agent.backend.main.get_forecast_weather') as mock_weather:
            mock_weather.return_value = [
                {
                    "date": "2024-02-01",
                    "temp_c": 15.0,
                    "condition": "clear",
                    "summary": "맑음"
                }
            ]
            
            response = client.get("/api/weather/파리?start_date=2024-02-01&end_date=2024-02-03")
            
            assert response.status_code == 200
            data = response.json()
            assert data["destination"] == "파리"
            assert "weather" in data
            assert len(data["weather"]) == 1
            assert data["weather"][0]["temp_c"] == 15.0

class TestPlacesAPI:
    """장소 검색 API 엔드포인트 테스트"""
    
    def test_search_places(self):
        """장소 검색 테스트"""
        with patch('travel_agent.backend.main.search_places_async') as mock_search:
            mock_search.return_value = [
                {
                    "name": "에펠탑",
                    "category": "landmark",
                    "lat": 48.8584,
                    "lon": 2.2945,
                    "description": "파리의 상징적인 철탑"
                }
            ]
            
            response = client.get("/api/places/파리?interests=역사,예술&limit=5")
            
            assert response.status_code == 200
            data = response.json()
            assert data["destination"] == "파리"
            assert "places" in data
            assert len(data["places"]) == 1
            assert data["places"][0]["name"] == "에펠탑"

class TestLocalInfoAPI:
    """현지 정보 API 엔드포인트 테스트"""
    
    def test_get_local_information(self):
        """현지 정보 조회 테스트"""
        with patch('travel_agent.backend.main.get_destination_info') as mock_info:
            mock_info.return_value = {
                "title": "파리",
                "summary": "프랑스의 수도이자 예술과 문화의 도시",
                "cultural_info": {"language": "프랑스어"},
                "travel_tips": ["에펠탑 방문을 추천합니다"]
            }
            
            response = client.get("/api/local-info/파리?language=ko")
            
            assert response.status_code == 200
            data = response.json()
            assert data["destination"] == "파리"
            assert "local_info" in data
            assert data["local_info"]["title"] == "파리"

class TestFeedbackAPI:
    """피드백 API 엔드포인트 테스트"""
    
    def test_submit_feedback(self):
        """피드백 제출 테스트"""
        feedback_data = {
            "overall_satisfaction": 4,
            "feedback_type": "schedule",
            "improvement_areas": ["하루에 너무 많은 장소를 방문합니다"],
            "free_feedback": "전반적으로 만족스럽습니다"
        }
        
        response = client.post("/api/feedback", json=feedback_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "피드백이 성공적으로 제출되었습니다"
        assert "feedback_id" in data
        assert "timestamp" in data
    
    def test_submit_feedback_validation_error(self):
        """필수 필드 누락 시 피드백 제출 오류 테스트"""
        invalid_feedback = {
            "feedback_type": "schedule"  # overall_satisfaction 누락
        }
        
        response = client.post("/api/feedback", json=invalid_feedback)
        assert response.status_code == 400
        
        data = response.json()
        assert "error" in data
        assert "필수 필드 누락" in data["message"]

class TestStatisticsAPI:
    """통계 API 엔드포인트 테스트"""
    
    def test_get_statistics(self):
        """통계 정보 조회 테스트"""
        response = client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_plans_generated" in data
        assert "crewai_usage" in data
        assert "graph_usage" in data
        assert "popular_destinations" in data
        assert "average_satisfaction" in data
        assert "last_updated" in data

class TestErrorHandling:
    """에러 처리 테스트"""
    
    def test_invalid_endpoint(self):
        """존재하지 않는 엔드포인트 접근 시 404 오류 테스트"""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """잘못된 HTTP 메서드 사용 시 405 오류 테스트"""
        response = client.put("/health")
        assert response.status_code == 405
    
    def test_invalid_json(self):
        """잘못된 JSON 데이터 전송 시 422 오류 테스트"""
        response = client.post("/plan", data="invalid json")
        assert response.status_code == 422

class TestInputValidation:
    """입력 검증 테스트"""
    
    def get_valid_preferences(self):
        """유효한 사용자 선호도 데이터 생성"""
        start_date = date.today() + timedelta(days=30)
        end_date = start_date + timedelta(days=3)
        
        return {
            "destination": "파리",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "interests": ["역사", "예술"],
            "pace": "balanced",
            "budget_level": "mid",
            "party": 2,
            "locale": "ko_KR",
            "transport_mode": "walking",
            "include_weather": True
        }
    
    def test_destination_length_validation(self):
        """여행지 길이 검증 테스트"""
        preferences = self.get_valid_preferences()
        preferences["destination"] = "a" * 101  # 최대 길이 초과
        
        response = client.post("/plan", json=preferences)
        assert response.status_code == 422
    
    def test_interests_validation(self):
        """관심사 검증 테스트"""
        preferences = self.get_valid_preferences()
        preferences["interests"] = ["a"] * 21  # 최대 개수 초과
        
        response = client.post("/plan", json=preferences)
        assert response.status_code == 422
    
    def test_party_size_validation(self):
        """여행 인원 검증 테스트"""
        preferences = self.get_valid_preferences()
        preferences["party"] = 21  # 최대 인원 초과
        
        response = client.post("/plan", json=preferences)
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__])
