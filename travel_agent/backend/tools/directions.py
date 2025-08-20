from __future__ import annotations
import httpx
import asyncio
from typing import Dict, List, Optional, Tuple
from math import radians, cos, sin, asin, sqrt
from ..config import settings
import logging
import json

# 로깅 설정
logger = logging.getLogger(__name__)

class DirectionsService:
    """Google Maps Directions API를 사용한 경로 계산 서비스"""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api/directions/json"
        self.timeout = 15
        
        # 교통수단별 속도 (km/h)
        self.transport_speeds = {
            "walking": 4.0,      # 도보: 4km/h
            "bicycling": 15.0,   # 자전거: 15km/h
            "transit": 25.0,     # 대중교통: 25km/h
            "driving": 40.0,     # 자동차: 40km/h (도시 내)
            "default": 4.0       # 기본값: 도보
        }
    
    async def get_directions(self, origin: Tuple[float, float], 
                           destination: Tuple[float, float], 
                           mode: str = "walking") -> Optional[Dict]:
        """Google Maps API를 사용한 경로 계산"""
        if not self.api_key:
            logger.warning("Google Maps API 키가 설정되지 않았습니다. Haversine 거리 계산을 사용합니다.")
            return self._calculate_haversine_route(origin, destination, mode)
        
        try:
            params = {
                "origin": f"{origin[0]},{origin[1]}",
                "destination": f"{destination[0]},{destination[1]}",
                "mode": mode,
                "key": self.api_key,
                "language": "ko",  # 한국어
                "units": "metric"   # 미터법
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("status") == "OK":
                    return self._parse_google_directions(data, mode)
                else:
                    logger.warning(f"Google Directions API 오류: {data.get('status')}")
                    return self._calculate_haversine_route(origin, destination, mode)
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"Google Maps API HTTP 오류: {e.response.status_code}")
            return self._calculate_haversine_route(origin, destination, mode)
        except httpx.RequestError as e:
            logger.error(f"Google Maps API 요청 오류: {e}")
            return self._calculate_haversine_route(origin, destination, mode)
        except Exception as e:
            logger.error(f"경로 계산 중 예상치 못한 오류: {e}")
            return self._calculate_haversine_route(origin, destination, mode)
    
    async def get_route_between_places(self, places: List[Tuple[str, float, float]], 
                                     mode: str = "walking") -> List[Dict]:
        """여러 장소 간의 경로 계산"""
        routes = []
        
        for i in range(len(places) - 1):
            current = places[i]
            next_place = places[i + 1]
            
            origin = (current[1], current[2])  # (lat, lon)
            destination = (next_place[1], next_place[2])
            
            route = await self.get_directions(origin, destination, mode)
            if route:
                route["from_place"] = current[0]
                route["to_place"] = next_place[0]
                routes.append(route)
        
        return routes
    
    def _parse_google_directions(self, data: Dict, mode: str) -> Dict:
        """Google Directions API 응답 파싱"""
        try:
            route = data.get("routes", [{}])[0]
            leg = route.get("legs", [{}])[0]
            
            # 기본 정보
            distance = leg.get("distance", {}).get("value", 0) / 1000  # m to km
            duration = leg.get("duration", {}).get("value", 0) / 60    # s to min
            
            # 상세 경로 정보
            steps = []
            for step in leg.get("steps", []):
                steps.append({
                    "instruction": step.get("html_instructions", "").replace("<b>", "").replace("</b>", ""),
                    "distance": step.get("distance", {}).get("text", ""),
                    "duration": step.get("duration", {}).get("text", ""),
                    "travel_mode": step.get("travel_mode", mode)
                })
            
            # 교통 정보 (대중교통인 경우)
            transit_info = None
            if mode == "transit" and leg.get("transit_details"):
                transit = leg["transit_details"]
                transit_info = {
                    "line": transit.get("line", {}).get("name", ""),
                    "departure_stop": transit.get("departure_stop", {}).get("name", ""),
                    "arrival_stop": transit.get("arrival_stop", {}).get("name", ""),
                    "departure_time": transit.get("departure_time", {}).get("text", ""),
                    "arrival_time": transit.get("arrival_time", {}).get("text", "")
                }
            
            return {
                "distance_km": round(distance, 2),
                "travel_min": int(duration),
                "mode": mode,
                "steps": steps,
                "transit_info": transit_info,
                "polyline": route.get("overview_polyline", {}).get("points", ""),
                "warnings": route.get("warnings", []),
                "fare": route.get("fare", {}).get("text", "") if mode == "transit" else None
            }
            
        except Exception as e:
            logger.error(f"Google Directions 응답 파싱 오류: {e}")
            return {}
    
    def _calculate_haversine_route(self, origin: Tuple[float, float], 
                                 destination: Tuple[float, float], 
                                 mode: str = "walking") -> Dict:
        """Haversine 공식을 사용한 거리 계산 (폴백)"""
        try:
            distance = haversine_km(origin[0], origin[1], destination[0], destination[1])
            travel_time = estimate_walk_minutes(distance, self.transport_speeds.get(mode, self.transport_speeds["default"]))
            
            return {
                "distance_km": round(distance, 2),
                "travel_min": travel_time,
                "mode": mode,
                "steps": [{
                    "instruction": f"{origin}에서 {destination}까지 직선 경로",
                    "distance": f"{round(distance, 2)}km",
                    "duration": f"{travel_time}분",
                    "travel_mode": mode
                }],
                "transit_info": None,
                "polyline": "",
                "warnings": ["Haversine 거리 계산 사용 (정확한 경로가 아닙니다)"],
                "fare": None
            }
            
        except Exception as e:
            logger.error(f"Haversine 경로 계산 오류: {e}")
            return {}
    
    async def optimize_route(self, places: List[Tuple[str, float, float]], 
                           mode: str = "walking") -> Tuple[List[Tuple[str, float, float]], List[Dict]]:
        """여러 장소를 방문하는 최적 경로 계산 (간단한 그리디 알고리즘)"""
        if len(places) <= 2:
            routes = await self.get_route_between_places(places, mode)
            return places, routes
        
        # 첫 번째 장소를 시작점으로 설정
        optimized_places = [places[0]]
        remaining_places = places[1:]
        total_distance = 0
        all_routes = []
        
        while remaining_places:
            current = optimized_places[-1]
            current_pos = (current[1], current[2])
            
            # 현재 위치에서 가장 가까운 다음 장소 찾기
            nearest_idx = 0
            min_distance = float('inf')
            
            for i, place in enumerate(remaining_places):
                place_pos = (place[1], place[2])
                distance = haversine_km(current_pos[0], current_pos[1], place_pos[0], place_pos[1])
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_idx = i
            
            # 가장 가까운 장소를 다음 방문지로 선택
            next_place = remaining_places[nearest_idx]
            optimized_places.append(next_place)
            remaining_places.pop(nearest_idx)
            
            # 경로 계산
            route = await self.get_directions(
                (current[1], current[2]), 
                (next_place[1], next_place[2]), 
                mode
            )
            
            if route:
                route["from_place"] = current[0]
                route["to_place"] = next_place[0]
                all_routes.append(route)
                total_distance += route["distance_km"]
        
        logger.info(f"최적화된 경로 총 거리: {total_distance:.2f}km")
        return optimized_places, all_routes
    
    def get_transport_recommendations(self, distance_km: float, 
                                    weather_condition: str = "clear") -> List[str]:
        """거리와 날씨를 고려한 교통수단 추천"""
        recommendations = []
        
        if distance_km <= 1.0:
            recommendations.append("도보 (가장 건강하고 경제적)")
            if weather_condition in ["clear", "cloudy"]:
                recommendations.append("자전거 (빠르고 효율적)")
        elif distance_km <= 3.0:
            if weather_condition in ["clear", "cloudy"]:
                recommendations.append("자전거 (권장)")
            recommendations.append("도보 (운동 효과)")
            recommendations.append("대중교통 (편리함)")
        elif distance_km <= 10.0:
            recommendations.append("대중교통 (가장 효율적)")
            if weather_condition in ["clear", "cloudy"]:
                recommendations.append("자전거 (운동 효과)")
        else:
            recommendations.append("대중교통 (장거리 이동)")
            recommendations.append("자동차 (편의성)")
        
        # 날씨별 특별 고려사항
        if weather_condition in ["rain", "snow", "storm"]:
            recommendations.insert(0, "대중교통 (날씨 고려)")
            if "도보" in recommendations:
                recommendations.remove("도보")
            if "자전거" in recommendations:
                recommendations.remove("자전거")
        
        return recommendations

# 전역 DirectionsService 인스턴스
directions_service = DirectionsService()

# 기존 함수들과의 호환성을 위한 래퍼들
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine 공식을 사용한 두 지점 간 거리 계산 (km)"""
    r = 6371.0  # 지구 반지름 (km)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return r * c

def estimate_walk_minutes(km: float, kmph: float = 4.0) -> int:
    """거리를 기반으로 도보 시간 추정 (분)"""
    return max(1, int((km / kmph) * 60))

async def get_directions_async(origin: Tuple[float, float], 
                              destination: Tuple[float, float], 
                              mode: str = "walking") -> Optional[Dict]:
    """비동기 경로 계산"""
    return await directions_service.get_directions(origin, destination, mode)

async def optimize_route_async(places: List[Tuple[str, float, float]], 
                              mode: str = "walking") -> Tuple[List[Tuple[str, float, float]], List[Dict]]:
    """비동기 경로 최적화"""
    return await directions_service.optimize_route(places, mode)

def get_transport_recommendations(distance_km: float, 
                                weather_condition: str = "clear") -> List[str]:
    """교통수단 추천"""
    return directions_service.get_transport_recommendations(distance_km, weather_condition)
