from __future__ import annotations
import httpx
import asyncio
from typing import List, Dict, Optional
from ..config import settings
import logging
import json

# 로깅 설정
logger = logging.getLogger(__name__)

class PlacesService:
    """FourSquare API를 사용한 장소 검색 및 추천 서비스"""
    
    def __init__(self):
        self.api_key = settings.FOURSQUARE_API_KEY
        self.base_url = "https://api.foursquare.com/v3"
        self.timeout = 15
        
        # 카테고리별 FourSquare ID 매핑
        self.category_mapping = {
            "museum": "10000",           # 박물관
            "landmark": "16000",         # 랜드마크
            "park": "16032",             # 공원
            "restaurant": "13065",       # 레스토랑
            "cafe": "13032",             # 카페
            "shopping": "17000",         # 쇼핑
            "entertainment": "10000",    # 엔터테인먼트
            "culture": "10000",          # 문화
            "nature": "16000",           # 자연
            "history": "16000",          # 역사
            "art": "10000",              # 예술
            "architecture": "16000",     # 건축
            "religion": "16000",         # 종교
            "sports": "18000",           # 스포츠
            "nightlife": "13000"         # 나이트라이프
        }
        
        # 관심사별 카테고리 매핑
        self.interest_to_category = {
            "문화": ["museum", "culture", "art", "history"],
            "역사": ["museum", "landmark", "history", "architecture"],
            "자연": ["park", "nature", "landmark"],
            "미식": ["restaurant", "cafe"],
            "쇼핑": ["shopping"],
            "엔터테인먼트": ["entertainment", "nightlife"],
            "예술": ["museum", "art", "culture"],
            "건축": ["architecture", "landmark"],
            "종교": ["religion", "landmark"],
            "스포츠": ["sports", "park"],
            "카페": ["cafe"],
            "레스토랑": ["restaurant"]
        }
    
    async def search_places(self, destination: str, interests: List[str], 
                           limit: int = 20) -> List[Dict]:
        """관심사 기반 장소 검색"""
        if not self.api_key:
            logger.warning("FourSquare API 키가 설정되지 않았습니다. 데모 데이터를 반환합니다.")
            return self._get_demo_places(destination, interests, limit)
        
        try:
            # 관심사를 카테고리로 변환
            categories = self._interests_to_categories(interests)
            
            # 각 카테고리별로 장소 검색
            all_places = []
            for category in categories:
                places = await self._search_by_category(destination, category, limit // len(categories))
                all_places.extend(places)
            
            # 중복 제거 및 정렬
            unique_places = self._remove_duplicates(all_places)
            sorted_places = self._sort_by_relevance(unique_places, interests)
            
            return sorted_places[:limit]
            
        except Exception as e:
            logger.error(f"장소 검색 중 오류: {e}")
            return self._get_demo_places(destination, interests, limit)
    
    async def _search_by_category(self, destination: str, category: str, limit: int) -> List[Dict]:
        """카테고리별 장소 검색"""
        try:
            url = f"{self.base_url}/places/search"
            params = {
                "query": destination,
                "categories": self.category_mapping.get(category, "10000"),
                "limit": limit,
                "sort": "RATING"  # 평점 순으로 정렬
            }
            
            headers = {
                "Authorization": self.api_key,
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                return self._parse_foursquare_response(data, category)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"FourSquare API HTTP 오류: {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            logger.error(f"FourSquare API 요청 오류: {e}")
            return []
        except Exception as e:
            logger.error(f"카테고리별 장소 검색 중 오류: {e}")
            return []
    
    def _parse_foursquare_response(self, data: Dict, category: str) -> List[Dict]:
        """FourSquare API 응답 파싱"""
        places = []
        
        try:
            for result in data.get("results", []):
                place = {
                    "name": result.get("name", "알 수 없는 장소"),
                    "category": category,
                    "lat": result.get("geocodes", {}).get("main", {}).get("latitude", 0),
                    "lon": result.get("geocodes", {}).get("main", {}).get("longitude", 0),
                    "description": result.get("description", ""),
                    "rating": result.get("rating", 0),
                    "price_level": result.get("price", 0),
                    "website": result.get("link", ""),
                    "address": result.get("location", {}).get("formatted_address", ""),
                    "est_stay_min": self._estimate_stay_time(category, result)
                }
                
                # 위도/경도가 유효한 경우만 추가
                if place["lat"] and place["lon"]:
                    places.append(place)
                    
        except Exception as e:
            logger.error(f"FourSquare 응답 파싱 오류: {e}")
        
        return places
    
    def _interests_to_categories(self, interests: List[str]) -> List[str]:
        """관심사를 FourSquare 카테고리로 변환"""
        categories = set()
        
        for interest in interests:
            interest_lower = interest.lower()
            
            # 직접 매핑
            if interest_lower in self.interest_to_category:
                categories.update(self.interest_to_category[interest_lower])
            else:
                # 부분 매칭
                for key, cats in self.interest_to_category.items():
                    if interest_lower in key.lower() or key.lower() in interest_lower:
                        categories.update(cats)
        
        # 기본 카테고리 추가
        if not categories:
            categories = ["landmark", "museum", "restaurant"]
        
        return list(categories)
    
    def _estimate_stay_time(self, category: str, place_data: Dict) -> int:
        """카테고리별 예상 체류 시간 추정 (분)"""
        base_times = {
            "museum": 120,      # 박물관: 2시간
            "landmark": 60,     # 랜드마크: 1시간
            "park": 90,         # 공원: 1.5시간
            "restaurant": 60,   # 레스토랑: 1시간
            "cafe": 45,         # 카페: 45분
            "shopping": 120,    # 쇼핑: 2시간
            "entertainment": 90, # 엔터테인먼트: 1.5시간
            "culture": 90,      # 문화: 1.5시간
            "nature": 90,       # 자연: 1.5시간
            "history": 90,      # 역사: 1.5시간
            "art": 90,          # 예술: 1.5시간
            "architecture": 60, # 건축: 1시간
            "religion": 60,     # 종교: 1시간
            "sports": 120,      # 스포츠: 2시간
            "nightlife": 180    # 나이트라이프: 3시간
        }
        
        base_time = base_times.get(category, 60)
        
        # 평점에 따른 시간 조정
        rating = place_data.get("rating", 0)
        if rating >= 8.0:
            base_time = int(base_time * 1.2)  # 높은 평점: 20% 증가
        elif rating <= 6.0:
            base_time = int(base_time * 0.8)  # 낮은 평점: 20% 감소
        
        return base_time
    
    def _remove_duplicates(self, places: List[Dict]) -> List[Dict]:
        """중복 장소 제거 (이름 기준)"""
        seen_names = set()
        unique_places = []
        
        for place in places:
            name = place["name"].lower().strip()
            if name not in seen_names:
                seen_names.add(name)
                unique_places.append(place)
        
        return unique_places
    
    def _sort_by_relevance(self, places: List[Dict], interests: List[str]) -> List[Dict]:
        """관심사 기반 관련성 순으로 정렬"""
        def relevance_score(place):
            score = 0
            
            # 평점 점수 (0-10점)
            score += place.get("rating", 0)
            
            # 관심사 매칭 점수
            for interest in interests:
                interest_lower = interest.lower()
                if (interest_lower in place["name"].lower() or 
                    interest_lower in place.get("description", "").lower()):
                    score += 5
            
            # 카테고리 관련성 점수
            for interest in interests:
                if interest.lower() in self.interest_to_category:
                    if place["category"] in self.interest_to_category[interest.lower()]:
                        score += 3
            
            return score
        
        return sorted(places, key=relevance_score, reverse=True)
    
    def _get_demo_places(self, destination: str, interests: List[str], limit: int) -> List[Dict]:
        """API 키가 없거나 오류 발생 시 데모 데이터 반환"""
        demo_places = [
            {
                "name": f"{destination} 중앙 박물관",
                "category": "museum",
                "lat": 48.8606,
                "lon": 2.3376,
                "description": f"{destination}의 대표적인 박물관으로, 다양한 문화재와 예술 작품을 전시합니다.",
                "est_stay_min": 120,
                "rating": 4.5,
                "price_level": 2,
                "website": "",
                "address": f"{destination} 중앙가 123번지"
            },
            {
                "name": f"{destination} 대성당",
                "category": "landmark",
                "lat": 48.8530,
                "lon": 2.3499,
                "description": f"{destination}의 역사적인 대성당으로, 아름다운 건축물과 종교 예술을 감상할 수 있습니다.",
                "est_stay_min": 60,
                "rating": 5.0,
                "price_level": 1,
                "website": "",
                "address": f"{destination} 종교로 456번지"
            },
            {
                "name": f"{destination} 강변 산책로",
                "category": "park",
                "lat": 48.857,
                "lon": 2.354,
                "description": f"{destination}의 아름다운 강변을 따라 걷는 산책로로, 자연과 도시의 조화를 느낄 수 있습니다.",
                "est_stay_min": 45,
                "rating": 4.0,
                "price_level": None,
                "website": "",
                "address": f"{destination} 강변길 789번지"
            }
        ]
        
        # 관심사에 맞는 추가 데모 장소들
        if "미식" in interests or "레스토랑" in interests:
            demo_places.append({
                "name": f"{destination} 전통 레스토랑",
                "category": "restaurant",
                "lat": 48.8580,
                "lon": 2.3480,
                "description": f"{destination}의 전통 요리를 맛볼 수 있는 레스토랑입니다.",
                "est_stay_min": 60,
                "rating": 4.8,
                "price_level": 3,
                "website": "",
                "address": f"{destination} 미식가 101번지"
            })
        
        if "쇼핑" in interests:
            demo_places.append({
                "name": f"{destination} 쇼핑 센터",
                "category": "shopping",
                "lat": 48.8590,
                "lon": 2.3500,
                "description": f"{destination}의 다양한 상품을 구매할 수 있는 쇼핑 센터입니다.",
                "est_stay_min": 120,
                "rating": 4.5,
                "price_level": 2,
                "website": "",
                "address": f"{destination} 쇼핑로 202번지"
            })
        
        return demo_places[:limit]

# 전역 PlacesService 인스턴스
places_service = PlacesService()

# 기존 함수와의 호환성을 위한 래퍼
def get_candidate_places(destination: str, interests: list[str]) -> List[Dict]:
    """기존 코드와의 호환성을 위한 함수"""
    # 동기 함수로 실행 (기존 코드 호환성)
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(places_service.search_places(destination, interests))
    except RuntimeError:
        # 새로운 이벤트 루프 생성
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(places_service.search_places(destination, interests))
        finally:
            loop.close()

async def search_places_async(destination: str, interests: List[str], limit: int = 20) -> List[Dict]:
    """비동기 장소 검색"""
    return await places_service.search_places(destination, interests, limit)
