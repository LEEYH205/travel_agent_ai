from __future__ import annotations
from crewai import Agent
from typing import List, Dict, Any
from datetime import datetime, timedelta
from ..schemas import UserPreferences, Place, DayPlan, Transfer
from ..tools.directions import haversine_km, estimate_walk_minutes

class ItineraryPlannerAgent:
    """사용자 선호도와 제약 조건을 고려한 최적의 여행 일정을 계획하는 Agent"""
    
    def __init__(self):
        self.agent = Agent(
            role="Itinerary Planner",
            goal="사용자의 여행 스타일, 시간, 이동 거리를 고려하여 최적의 일별 여행 계획을 수립합니다",
            backstory="""당신은 여행 일정 계획의 전문가입니다. 
            각 관광지의 특성, 이동 시간, 운영 시간, 사용자 선호도를 종합적으로 분석하여 
            효율적이고 만족도 높은 여행 일정을 만들어냅니다.
            하루의 흐름을 자연스럽게 연결하고, 피로도를 최소화하면서 
            최대한 많은 경험을 할 수 있도록 계획합니다.""",
            verbose=True,
            allow_delegation=False
        )
    
    async def plan_days(self, preferences: UserPreferences, places: List[Place], 
                       research_data: Dict[str, Any] = None) -> List[DayPlan]:
        """여행 일정 계획 수립"""
        try:
            # 1. 기본 일정 계획
            basic_plan = self._create_basic_plan(preferences, places)
            
            # 2. 여행 스타일에 따른 일정 최적화
            optimized_plan = self._optimize_for_travel_style(basic_plan, preferences.pace)
            
            # 3. 날씨를 고려한 일정 조정
            if research_data and research_data.get('weather'):
                weather_adjusted = self._adjust_for_weather(optimized_plan, research_data['weather'])
            else:
                weather_adjusted = optimized_plan
            
            # 4. 이동 경로 최적화
            final_plan = self._optimize_routes(weather_adjusted)
            
            # 5. 식사 시간 및 휴식 시간 추가
            complete_plan = self._add_meals_and_breaks(final_plan, preferences)
            
            return complete_plan
            
        except Exception as e:
            raise ValueError(f"일정 계획 수립 중 오류 발생: {str(e)}")
    
    def _create_basic_plan(self, preferences: UserPreferences, places: List[Place]) -> List[DayPlan]:
        """기본 일정 계획 생성"""
        start = datetime.fromisoformat(preferences.start_date)
        end = datetime.fromisoformat(preferences.end_date)
        num_days = (end - start).days + 1
        
        # 장소가 없는 경우 기본 일정 생성
        if not places:
            return self._create_fallback_plan(preferences, num_days, start)
        
        # 하루당 방문할 명소 수 계산
        if preferences.pace == "relaxed":
            per_day = max(2, min(4, len(places) // max(1, num_days)))
        elif preferences.pace == "packed":
            per_day = max(4, min(6, len(places) // max(1, num_days)))
        else:  # balanced
            per_day = max(3, min(5, len(places) // max(1, num_days)))
        
        days: List[DayPlan] = []
        place_idx = 0
        
        for i in range(num_days):
            current_date = start + timedelta(days=i)
            
            # 해당 날짜에 방문할 명소 선택
            day_places = places[place_idx:place_idx + per_day]
            place_idx += per_day
            
            # 명소가 부족한 경우 루프
            if place_idx >= len(places) and places:
                place_idx = 0
                # 남은 장소가 부족하면 첫 번째 장소라도 추가
                if not day_places and places:
                    day_places = [places[0]]
            
            # 시간대별 명소 배치
            morning_places = day_places[:1] if day_places else []
            afternoon_places = day_places[1:2] if len(day_places) > 1 else []
            evening_places = day_places[2:] if len(day_places) > 2 else []
            
            # 이동 경로 계산
            transfers = self._calculate_transfers(day_places)
            
            day_plan = DayPlan(
                date=current_date.date().isoformat(),
                morning=morning_places,
                lunch=None,  # 나중에 추가
                afternoon=afternoon_places,
                dinner=None,  # 나중에 추가
                evening=evening_places,
                transfers=transfers
            )
            
            days.append(day_plan)
        
        return days
    
    def _create_fallback_plan(self, preferences: UserPreferences, num_days: int, start: datetime) -> List[DayPlan]:
        """장소 정보가 없는 경우 기본 일정 생성"""
        days: List[DayPlan] = []
        
        # 기본 임시 장소 생성
        fallback_place = Place(
            name=f"{preferences.destination} 관광",
            category="general",
            lat=0.0,
            lon=0.0,
            description=f"{preferences.destination} 지역 탐방",
            est_stay_min=180  # 3시간
        )
        
        for i in range(num_days):
            current_date = start + timedelta(days=i)
            
            day_plan = DayPlan(
                date=current_date.date().isoformat(),
                morning=[fallback_place],
                lunch=f"{preferences.destination} 현지 음식 체험",
                afternoon=[],
                dinner=f"{preferences.destination} 저녁 식사",
                evening=[],
                transfers=[]
            )
            
            days.append(day_plan)
        
        return days
    
    def _optimize_for_travel_style(self, plan: List[DayPlan], pace: str) -> List[DayPlan]:
        """여행 스타일에 따른 일정 최적화"""
        if pace == "relaxed":
            # 여유로운 여행: 하루 명소 수 줄이고 체류 시간 증가
            for day in plan:
                # 오전/오후/저녁 각각 최대 2개씩으로 제한
                day.morning = day.morning[:2]
                day.afternoon = day.afternoon[:2]
                day.evening = day.evening[:2]
        elif pace == "packed":
            # 빡빡한 여행: 하루에 더 많은 명소 방문
            for day in plan:
                # 각 시간대별로 더 많은 명소 배치
                day.morning = day.morning[:3]
                day.afternoon = day.afternoon[:3]
                day.evening = day.evening[:3]
        
        return plan
    
    def _adjust_for_weather(self, plan: List[DayPlan], weather_data: List[Dict]) -> List[DayPlan]:
        """날씨를 고려한 일정 조정"""
        for i, day in enumerate(plan):
            if i < len(weather_data):
                weather = weather_data[i]
                condition = weather.get('condition', 'clear')
                
                # 날씨가 좋지 않은 경우 실내 명소 우선 배치
                if condition in ['rain', 'snow', 'storm']:
                    # 실내 명소를 오전으로 이동
                    indoor_places = [p for p in day.morning + day.afternoon + day.evening 
                                   if p.category in ['museum', 'gallery', 'shopping', 'restaurant']]
                    outdoor_places = [p for p in day.morning + day.afternoon + day.evening 
                                    if p.category not in ['museum', 'gallery', 'shopping', 'restaurant']]
                    
                    # 실내 명소를 오전에 집중 배치
                    day.morning = indoor_places[:2]
                    day.afternoon = outdoor_places[:2] if outdoor_places else indoor_places[2:4]
                    day.evening = outdoor_places[2:4] if len(outdoor_places) > 2 else indoor_places[4:6]
        
        return plan
    
    def _optimize_routes(self, plan: List[DayPlan]) -> List[DayPlan]:
        """이동 경로 최적화"""
        for day in plan:
            all_places = day.morning + day.afternoon + day.evening
            if len(all_places) < 2:
                continue
            
            # 명소 간 거리를 고려한 순서 최적화 (간단한 그리디 알고리즘)
            optimized_order = self._optimize_place_order(all_places)
            
            # 최적화된 순서로 재배치
            day.morning = optimized_order[:len(day.morning)]
            day.afternoon = optimized_order[len(day.morning):len(day.morning) + len(day.afternoon)]
            day.evening = optimized_order[len(day.morning) + len(day.afternoon):]
            
            # 새로운 이동 경로 계산
            day.transfers = self._calculate_transfers(optimized_order)
        
        return plan
    
    def _optimize_place_order(self, places: List[Place]) -> List[Place]:
        """명소 방문 순서 최적화 (간단한 그리디 알고리즘)"""
        if len(places) <= 1:
            return places
        
        # 첫 번째 명소는 그대로
        optimized = [places[0]]
        remaining = places[1:]
        
        while remaining:
            current = optimized[-1]
            # 현재 위치에서 가장 가까운 다음 명소 찾기
            nearest_idx = 0
            min_distance = float('inf')
            
            for i, place in enumerate(remaining):
                distance = haversine_km(current.lat, current.lon, place.lat, place.lon)
                if distance < min_distance:
                    min_distance = distance
                    nearest_idx = i
            
            # 가장 가까운 명소를 다음 방문지로 선택
            optimized.append(remaining[nearest_idx])
            remaining.pop(nearest_idx)
        
        return optimized
    
    def _calculate_transfers(self, places: List[Place]) -> List[Transfer]:
        """명소 간 이동 경로 계산"""
        transfers = []
        
        for i in range(len(places) - 1):
            current = places[i]
            next_place = places[i + 1]
            
            distance = haversine_km(current.lat, current.lon, next_place.lat, next_place.lon)
            travel_time = estimate_walk_minutes(distance)
            
            transfer = Transfer(
                from_place=current.name,
                to_place=next_place.name,
                travel_min=travel_time,
                distance_km=round(distance, 2),
                mode="walk"  # 기본값은 도보
            )
            
            transfers.append(transfer)
        
        return transfers
    
    def _add_meals_and_breaks(self, plan: List[DayPlan], preferences: UserPreferences) -> List[DayPlan]:
        """식사 시간과 휴식 시간 추가"""
        for day in plan:
            # 점심 시간 추가 (오전 명소 방문 후)
            if day.morning:
                day.lunch = f"{day.morning[-1].name} 근처에서 점심 식사"
            
            # 저녁 시간 추가 (오후 명소 방문 후)
            if day.afternoon:
                day.dinner = f"{day.afternoon[-1].name} 근처에서 저녁 식사"
            
            # 휴식 시간 고려 (여행 스타일에 따라)
            if preferences.pace == "relaxed":
                # 여유로운 여행: 휴식 시간 추가
                if day.morning and day.afternoon:
                    day.afternoon.insert(0, Place(
                        name="카페에서 휴식",
                        category="restaurant",
                        lat=0, lon=0,
                        description="오전 관광 후 휴식",
                        est_stay_min=30
                    ))
        
        return plan
    
    def get_itinerary_summary(self, plan: List[DayPlan]) -> str:
        """일정 요약 정보 생성"""
        if not plan:
            return "일정을 계획할 수 없습니다."
        
        summary = f"총 {len(plan)}일간의 여행 일정을 계획했습니다:\n\n"
        
        for day in plan:
            summary += f"📅 {day.date}\n"
            
            if day.morning:
                summary += f"🌅 오전: {', '.join([p.name for p in day.morning])}\n"
            if day.lunch:
                summary += f"🍽️ 점심: {day.lunch}\n"
            if day.afternoon:
                summary += f"🌞 오후: {', '.join([p.name for p in day.afternoon])}\n"
            if day.dinner:
                summary += f"🍽️ 저녁: {day.dinner}\n"
            if day.evening:
                summary += f"🌙 저녁: {', '.join([p.name for p in day.evening])}\n"
            
            if day.transfers:
                total_time = sum(t.travel_min for t in day.transfers)
                total_distance = sum(t.distance_km for t in day.transfers)
                summary += f"🚶 이동: 총 {total_time}분, {total_distance:.1f}km\n"
            
            summary += "\n"
        
        return summary

# 기존 함수와의 호환성을 위한 래퍼
def plan_days(pref: UserPreferences, places: List[Place]) -> List[DayPlan]:
    """기존 코드와의 호환성을 위한 함수"""
    agent = ItineraryPlannerAgent()
    # 동기 함수로 실행 (기존 코드 호환성)
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(agent.plan_days(pref, places))
    except RuntimeError:
        # 새로운 이벤트 루프 생성
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(agent.plan_days(pref, places))
        finally:
            loop.close()
