from __future__ import annotations
import httpx
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from ..config import settings
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

class WeatherService:
    """OpenWeather API를 사용한 날씨 정보 서비스"""
    
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.timeout = 10
        
    async def get_current_weather(self, lat: float, lon: float) -> Optional[Dict]:
        """현재 날씨 정보 조회"""
        if not self.api_key:
            logger.warning("OpenWeather API 키가 설정되지 않았습니다. 데모 데이터를 반환합니다.")
            return self._get_demo_weather("current")
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric",  # 섭씨 온도
                "lang": "kr"        # 한국어
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                return self._parse_current_weather(data)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenWeather API HTTP 오류: {e.response.status_code}")
            return self._get_demo_weather("current")
        except httpx.RequestError as e:
            logger.error(f"OpenWeather API 요청 오류: {e}")
            return self._get_demo_weather("current")
        except Exception as e:
            logger.error(f"날씨 정보 조회 중 예상치 못한 오류: {e}")
            return self._get_demo_weather("current")
    
    async def get_forecast_weather(self, lat: float, lon: float, days: int = 7) -> List[Dict]:
        """일기 예보 정보 조회 (최대 7일)"""
        if not self.api_key:
            logger.warning("OpenWeather API 키가 설정되지 않았습니다. 데모 데이터를 반환합니다.")
            return [self._get_demo_weather("forecast") for _ in range(days)]
        
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric",
                "lang": "kr",
                "cnt": min(days * 8, 40)  # 3시간마다 데이터, 최대 40개
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                return self._parse_forecast_weather(data, days)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenWeather API HTTP 오류: {e.response.status_code}")
            return [self._get_demo_weather("forecast") for _ in range(days)]
        except httpx.RequestError as e:
            logger.error(f"OpenWeather API 요청 오류: {e}")
            return [self._get_demo_weather("forecast") for _ in range(days)]
        except Exception as e:
            logger.error(f"일기 예보 조회 중 예상치 못한 오류: {e}")
            return [self._get_demo_weather("forecast") for _ in range(days)]
    
    async def get_daily_weather(self, lat: float, lon: float, date: str) -> Dict:
        """특정 날짜의 날씨 정보 조회"""
        try:
            target_date = datetime.fromisoformat(date)
            today = datetime.now().date()
            
            # 오늘 날짜인 경우 현재 날씨 반환
            if target_date.date() == today:
                current_weather = await self.get_current_weather(lat, lon)
                if current_weather:
                    return {
                        "date": date,
                        "summary": current_weather["summary"],
                        "temp_c": current_weather["temp_c"],
                        "condition": current_weather["condition"],
                        "humidity": current_weather["humidity"],
                        "wind_speed": current_weather["wind_speed"],
                        "icon": current_weather["icon"]
                    }
            
            # 미래 날짜인 경우 예보에서 해당 날짜 찾기
            forecast = await self.get_forecast_weather(lat, lon, 7)
            for day_weather in forecast:
                if day_weather["date"] == date:
                    return day_weather
            
            # 해당 날짜를 찾을 수 없는 경우 데모 데이터 반환
            logger.warning(f"날짜 {date}에 대한 날씨 정보를 찾을 수 없습니다.")
            return self._get_demo_weather("daily")
            
        except Exception as e:
            logger.error(f"일일 날씨 정보 조회 중 오류: {e}")
            return self._get_demo_weather("daily")
    
    def _parse_current_weather(self, data: Dict) -> Dict:
        """OpenWeather API 응답 파싱 (현재 날씨)"""
        try:
            weather = data.get("weather", [{}])[0]
            main = data.get("main", {})
            wind = data.get("wind", {})
            
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "summary": weather.get("description", "알 수 없음"),
                "temp_c": round(main.get("temp", 0)),
                "feels_like_c": round(main.get("feels_like", 0)),
                "condition": self._map_weather_condition(weather.get("main", "")),
                "humidity": main.get("humidity", 0),
                "wind_speed": round(wind.get("speed", 0) * 3.6, 1),  # m/s to km/h
                "icon": weather.get("icon", ""),
                "pressure": main.get("pressure", 0),
                "visibility": data.get("visibility", 0)
            }
        except Exception as e:
            logger.error(f"현재 날씨 데이터 파싱 오류: {e}")
            return self._get_demo_weather("current")
    
    def _parse_forecast_weather(self, data: Dict, days: int) -> List[Dict]:
        """OpenWeather API 응답 파싱 (일기 예보)"""
        try:
            daily_forecasts = []
            processed_dates = set()
            
            for item in data.get("list", []):
                date = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
                
                # 이미 처리된 날짜는 건너뛰기
                if date in processed_dates:
                    continue
                
                weather = item.get("weather", [{}])[0]
                main = item.get("main", {})
                
                daily_forecast = {
                    "date": date,
                    "summary": weather.get("description", "알 수 없음"),
                    "temp_c": round(main.get("temp", 0)),
                    "temp_min": round(main.get("temp_min", 0)),
                    "temp_max": round(main.get("temp_max", 0)),
                    "condition": self._map_weather_condition(weather.get("main", "")),
                    "humidity": main.get("humidity", 0),
                    "icon": weather.get("icon", "")
                }
                
                daily_forecasts.append(daily_forecast)
                processed_dates.add(date)
                
                # 요청한 일수만큼 수집
                if len(daily_forecasts) >= days:
                    break
            
            return daily_forecasts
            
        except Exception as e:
            logger.error(f"일기 예보 데이터 파싱 오류: {e}")
            return [self._get_demo_weather("forecast") for _ in range(days)]
    
    def _map_weather_condition(self, condition: str) -> str:
        """OpenWeather 조건을 내부 조건으로 매핑"""
        condition_mapping = {
            "Clear": "clear",
            "Clouds": "cloudy",
            "Rain": "rain",
            "Drizzle": "rain",
            "Thunderstorm": "storm",
            "Snow": "snow",
            "Mist": "fog",
            "Fog": "fog",
            "Haze": "fog",
            "Smoke": "fog",
            "Dust": "fog",
            "Sand": "fog",
            "Ash": "fog",
            "Squall": "windy",
            "Tornado": "storm"
        }
        return condition_mapping.get(condition, "unknown")
    
    def _get_demo_weather(self, weather_type: str) -> Dict:
        """API 키가 없거나 오류 발생 시 데모 데이터 반환"""
        if weather_type == "current":
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "summary": "(데모) 맑음, 구름 조금",
                "temp_c": 22,
                "feels_like_c": 24,
                "condition": "clear",
                "humidity": 65,
                "wind_speed": 12.0,
                "icon": "01d",
                "pressure": 1013,
                "visibility": 10000
            }
        elif weather_type == "forecast":
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "summary": "(데모) 맑음",
                "temp_c": 22,
                "temp_min": 18,
                "temp_max": 26,
                "condition": "clear",
                "humidity": 65,
                "icon": "01d"
            }
        else:  # daily
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "summary": "(데모) 온화함, 구름 조금",
                "temp_c": 20,
                "condition": "clear",
                "humidity": 65,
                "wind_speed": 10.0,
                "icon": "01d"
            }

# 전역 WeatherService 인스턴스
weather_service = WeatherService()

# 기존 함수와의 호환성을 위한 래퍼
async def get_daily_weather(lat: float, lon: float, date: str) -> dict:
    """기존 코드와의 호환성을 위한 함수"""
    return await weather_service.get_daily_weather(lat, lon, date)

async def get_current_weather(lat: float, lon: float) -> dict:
    """현재 날씨 정보 조회"""
    return await weather_service.get_current_weather(lat, lon)

async def get_forecast_weather(lat: float, lon: float, days: int = 7) -> List[Dict]:
    """일기 예보 정보 조회"""
    return await weather_service.get_forecast_weather(lat, lon, days)
