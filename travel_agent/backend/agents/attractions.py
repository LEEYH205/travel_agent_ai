from __future__ import annotations
from crewai import Agent
from typing import List, Dict, Any
from ..tools.places import get_candidate_places
from ..schemas import Place, UserPreferences

class AttractionsAgent:
    """사용자 관심사와 선호도에 맞는 관광명소를 선별하는 Agent"""
    
    def __init__(self):
        self.agent = Agent(
            role="Attractions Specialist",
            goal="사용자의 관심사, 여행 스타일, 예산에 맞는 최적의 관광명소를 선별하고 추천합니다",
            backstory="""당신은 여행지의 관광명소 전문가입니다. 
            각 지역의 숨겨진 명소부터 대표적인 관광지를 모두 알고 있으며, 
            사용자의 취향과 여행 스타일에 맞는 맞춤형 추천을 제공합니다.
            문화, 역사, 자연, 엔터테인먼트 등 다양한 카테고리의 명소를 
            균형있게 조합하여 완벽한 여행 경험을 만들어냅니다.""",
            verbose=True,
            allow_delegation=False
        )
    
    async def select_attractions(self, destination: str, preferences: UserPreferences, 
                               research_data: Dict[str, Any] = None) -> List[Place]:
        """사용자 선호도에 맞는 관광명소 선별"""
        try:
            # 1. 기본 명소 후보 수집
            base_places = get_candidate_places(destination, preferences.interests)
            
            # 2. 사용자 선호도 기반 필터링
            filtered_places = self._filter_by_preferences(base_places, preferences)
            
            # 3. 여행 스타일에 따른 명소 조합 최적화
            optimized_places = self._optimize_for_travel_style(
                filtered_places, preferences.pace, preferences.budget_level
            )
            
            # 4. 날씨와 시즌을 고려한 명소 선별
            if research_data and research_data.get('weather'):
                weather_optimized = self._optimize_for_weather(
                    optimized_places, research_data['weather']
                )
            else:
                weather_optimized = optimized_places
            
            # 5. 최종 명소 리스트 구성
            final_places = self._create_final_selection(
                weather_optimized, preferences, research_data
            )
            
            return final_places
            
        except Exception as e:
            raise ValueError(f"관광명소 선별 중 오류 발생: {str(e)}")
    
    def _filter_by_preferences(self, places: List[Dict], preferences: UserPreferences) -> List[Dict]:
        """사용자 선호도 기반 필터링"""
        filtered = []
        
        for place in places:
            score = 0
            
            # 관심사 매칭 점수
            if preferences.interests:
                for interest in preferences.interests:
                    if interest.lower() in place.get('description', '').lower():
                        score += 2
                    if interest.lower() in place.get('category', '').lower():
                        score += 1
            
            # 예산 수준 고려
            if preferences.budget_level == 'low' and place.get('price_level', 0) <= 1:
                score += 1
            elif preferences.budget_level == 'mid' and place.get('price_level', 0) <= 2:
                score += 1
            elif preferences.budget_level == 'high':
                score += 1
            
            # 점수가 기준 이상인 명소만 선택
            if score >= 1:
                filtered.append({**place, 'preference_score': score})
        
        # 점수 순으로 정렬
        filtered.sort(key=lambda x: x.get('preference_score', 0), reverse=True)
        return filtered
    
    def _optimize_for_travel_style(self, places: List[Dict], pace: str, budget: str) -> List[Dict]:
        """여행 스타일에 따른 최적화"""
        if pace == "relaxed":
            # 여유로운 여행: 명소 수를 줄이고 체류 시간이 긴 곳 위주
            return [p for p in places if p.get('est_stay_min', 60) >= 90][:8]
        elif pace == "packed":
            # 빡빡한 여행: 다양한 명소를 빠르게 돌아볼 수 있는 곳
            return [p for p in places if p.get('est_stay_min', 60) <= 120][:12]
        else:  # balanced
            # 균형잡힌 여행: 다양한 유형의 명소를 조합
            return places[:10]
    
    def _optimize_for_weather(self, places: List[Dict], weather_data: List[Dict]) -> List[Dict]:
        """날씨를 고려한 명소 최적화"""
        weather_optimized = []
        
        for place in places:
            # 실내/실외 명소 구분 (간단한 예시)
            is_indoor = place.get('category') in ['museum', 'gallery', 'shopping', 'restaurant']
            
            # 날씨가 좋지 않은 날에는 실내 명소 우선
            bad_weather_days = [w for w in weather_data if w.get('condition') in ['rain', 'snow', 'storm']]
            
            if bad_weather_days and not is_indoor:
                place['weather_note'] = "날씨가 좋지 않을 수 있음"
            
            weather_optimized.append(place)
        
        return weather_optimized
    
    def _create_final_selection(self, places: List[Dict], preferences: UserPreferences, 
                               research_data: Dict[str, Any] = None) -> List[Place]:
        """최종 명소 리스트 생성"""
        final_places = []
        
        # 카테고리별 균형 조정
        categories = {}
        for place in places:
            cat = place.get('category', 'poi')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(place)
        
        # 각 카테고리에서 균형있게 선택
        max_per_category = max(1, len(places) // len(categories)) if categories else 3
        
        for category, category_places in categories.items():
            selected = category_places[:max_per_category]
            for place in selected:
                final_places.append(Place(**{
                    "name": place["name"],
                    "category": place.get("category", "poi"),
                    "lat": place["lat"],
                    "lon": place["lon"],
                    "description": place.get("description"),
                    "est_stay_min": place.get("est_stay_min", 60),
                    "url": place.get("url"),
                    "price_level": place.get("price_level", 0),
                    "weather_note": place.get("weather_note")
                }))
        
        return final_places[:len(places)]  # 원래 개수만큼 반환
    
    def get_attractions_summary(self, places: List[Place]) -> str:
        """선별된 명소 요약 정보 생성"""
        if not places:
            return "추천할 명소를 찾을 수 없습니다."
        
        categories = {}
        for place in places:
            cat = place.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(place.name)
        
        summary = f"총 {len(places)}개의 명소를 추천합니다:\n"
        for category, names in categories.items():
            summary += f"- {category}: {', '.join(names[:3])}\n"
            if len(names) > 3:
                summary += f"  외 {len(names) - 3}개\n"
        
        return summary

# 기존 함수와의 호환성을 위한 래퍼
async def select_attractions(destination: str, interests: List[str]) -> List[Place]:
    """기존 코드와의 호환성을 위한 함수"""
    agent = AttractionsAgent()
    # 간단한 UserPreferences 객체 생성
    from ..schemas import UserPreferences
    pref = UserPreferences(
        destination=destination,
        start_date="2024-01-01",  # 기본값
        end_date="2024-01-01",    # 기본값
        interests=interests
    )
    return await agent.select_attractions(destination, pref)
