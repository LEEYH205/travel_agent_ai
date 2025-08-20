from __future__ import annotations
from crewai import Agent
from ..tools.geocode import geocode_city
from ..tools.weather import get_daily_weather
from ..tools.wiki import get_destination_info
from ..schemas import UserPreferences
from datetime import datetime, timedelta
from typing import Dict, Any

class ResearchAgent:
    """여행지 정보 수집 및 분석을 담당하는 Agent"""
    
    def __init__(self):
        self.agent = Agent(
            role="Travel Destination Researcher",
            goal="여행지의 최신 정보, 날씨, 시즌별 특이사항을 종합적으로 수집하고 분석합니다",
            backstory="""당신은 여행 전문 연구원입니다. 
            세계 각지의 여행지에 대한 깊이 있는 지식을 가지고 있으며, 
            날씨, 문화, 축제, 시즌별 특이사항 등을 종합적으로 분석하여 
            여행 계획에 필요한 핵심 정보를 제공합니다.""",
            verbose=True,
            allow_delegation=False
        )
    
    async def run_research(self, pref: UserPreferences) -> Dict[str, Any]:
        """여행지 정보 수집 및 분석 실행"""
        try:
            # 1. 지리 정보 수집
            coords = geocode_city(pref.destination)
            if not coords:
                raise ValueError(f"목적지 '{pref.destination}'을 찾을 수 없습니다")
            
            lat, lon = coords
            
            # 2. 날씨 정보 수집
            start = datetime.fromisoformat(pref.start_date)
            end = datetime.fromisoformat(pref.end_date)
            weather_data = []
            
            d = start
            while d <= end:
                weather = await get_daily_weather(lat, lon, d.date().isoformat())
                weather_data.append(weather)
                d += timedelta(days=1)
            
            # 3. 여행지 기본 정보 수집
            destination_info = await get_destination_info(pref.destination)
            
            # 4. 시즌별 특이사항 분석
            season_analysis = self._analyze_season(start, end, pref.destination)
            
            return {
                "destination": pref.destination,
                "coordinates": {"lat": lat, "lon": lon},
                "weather": weather_data,
                "destination_info": destination_info,
                "season_analysis": season_analysis,
                "research_summary": self._generate_research_summary(
                    pref.destination, weather_data, destination_info, season_analysis
                )
            }
            
        except Exception as e:
            raise ValueError(f"여행지 정보 수집 중 오류 발생: {str(e)}")
    
    def _analyze_season(self, start: datetime, end: datetime, destination: str) -> Dict[str, Any]:
        """시즌별 특이사항 분석"""
        # 간단한 시즌 분석 로직
        month = start.month
        
        season_info = {
            "spring": [3, 4, 5],
            "summer": [6, 7, 8], 
            "autumn": [9, 10, 11],
            "winter": [12, 1, 2]
        }
        
        current_season = None
        for season, months in season_info.items():
            if month in months:
                current_season = season
                break
        
        # 여행지별 시즌 특이사항 (예시)
        seasonal_tips = {
            "파리": {
                "spring": "봄꽃이 만발하는 아름다운 시즌, 야외 카페 이용 추천",
                "summer": "여름 휴가 시즌, 관광객이 많음, 사전 예약 필수",
                "autumn": "가을 단풍이 아름다운 시즌, 박물관 관람 추천",
                "winter": "크리스마스 시즌, 쇼핑과 축제 분위기"
            }
        }
        
        return {
            "current_season": current_season,
            "seasonal_tips": seasonal_tips.get(destination, {}),
            "best_activities": self._get_seasonal_activities(current_season, destination)
        }
    
    def _get_seasonal_activities(self, season: str, destination: str) -> list:
        """시즌별 추천 활동"""
        activities = {
            "spring": ["야외 관광", "공원 산책", "봄 축제 참여"],
            "summer": ["야외 액티비티", "해변 휴식", "여름 축제"],
            "autumn": ["문화 관광", "자연 관찰", "가을 축제"],
            "winter": ["실내 관광", "겨울 스포츠", "크리스마스 이벤트"]
        }
        return activities.get(season, ["일반 관광"])
    
    def _generate_research_summary(self, destination: str, weather: list, 
                                 info: dict, season: dict) -> str:
        """연구 결과 요약 생성"""
        return f"""
        {destination} 여행 정보 요약:
        - 날씨: {len(weather)}일간 날씨 정보 수집 완료
        - 시즌: {season.get('current_season', '알 수 없음')} 시즌
        - 특이사항: {season.get('seasonal_tips', {}).get(season.get('current_season', ''), '해당 없음')}
        - 추천 활동: {', '.join(season.get('best_activities', []))}
        """

# 기존 함수와의 호환성을 위한 래퍼
async def run_research(pref: UserPreferences) -> dict:
    """기존 코드와의 호환성을 위한 함수"""
    agent = ResearchAgent()
    return await agent.run_research(pref)
