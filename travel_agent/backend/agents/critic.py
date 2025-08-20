from __future__ import annotations
from crewai import Agent
from typing import List, Dict, Any
from ..schemas import DayPlan, Itinerary, UserPreferences

class CriticAgent:
    """여행 계획의 품질을 검토하고 개선점을 제안하는 Agent"""
    
    def __init__(self):
        self.agent = Agent(
            role="Travel Critic",
            goal="여행 계획의 실현 가능성, 효율성, 만족도를 검토하고 구체적인 개선 방안을 제시합니다",
            backstory="""당신은 여행 계획의 품질을 검토하는 전문가입니다. 
            계획의 실현 가능성, 시간 배분의 적절성, 이동 거리의 효율성, 
            사용자 선호도와의 일치성을 종합적으로 분석합니다.
            문제점을 찾아내고 구체적이고 실용적인 개선 방안을 제시합니다.""",
            verbose=True,
            allow_delegation=False
        )
    
    async def review_itinerary(self, itinerary: Itinerary, preferences: UserPreferences) -> Dict[str, Any]:
        """여행 계획 전체 검토"""
        try:
            # 1. 기본 검증
            basic_issues = self._validate_basic_requirements(itinerary, preferences)
            
            # 2. 시간 배분 검토
            time_issues = self._review_time_allocation(itinerary, preferences)
            
            # 3. 이동 효율성 검토
            efficiency_issues = self._review_efficiency(itinerary)
            
            # 4. 사용자 선호도 일치성 검토
            preference_issues = self._review_preference_alignment(itinerary, preferences)
            
            # 5. 종합 평가 및 개선 제안
            overall_score = self._calculate_overall_score(basic_issues, time_issues, efficiency_issues, preference_issues)
            improvement_suggestions = self._generate_improvement_suggestions(
                basic_issues, time_issues, efficiency_issues, preference_issues
            )
            
            return {
                "overall_score": overall_score,
                "issues": {
                    "basic": basic_issues,
                    "time": time_issues,
                    "efficiency": efficiency_issues,
                    "preferences": preference_issues
                },
                "improvement_suggestions": improvement_suggestions,
                "is_acceptable": overall_score >= 7.0
            }
            
        except Exception as e:
            return {
                "overall_score": 0.0,
                "issues": {"error": [f"검토 중 오류 발생: {str(e)}"]},
                "improvement_suggestions": ["계획을 다시 검토해주세요"],
                "is_acceptable": False
            }
    
    def _validate_basic_requirements(self, itinerary: Itinerary, preferences: UserPreferences) -> List[str]:
        """기본 요구사항 검증"""
        issues = []
        
        # 1. 중복 장소 방문 확인
        seen_places = set()
        for day in itinerary.days:
            for place in day.morning + day.afternoon + day.evening:
                if place.name in seen_places:
                    issues.append(f"중복 방문: {place.name} (여러 날짜에 방문)")
                seen_places.add(place.name)
        
        # 2. 여행 기간 확인
        expected_days = len(itinerary.days)
        if expected_days == 0:
            issues.append("일정이 없습니다")
        
        # 3. 필수 정보 확인
        if not itinerary.summary:
            issues.append("여행 요약이 없습니다")
        
        if not itinerary.tips:
            issues.append("현지 팁이 없습니다")
        
        return issues
    
    def _review_time_allocation(self, itinerary: Itinerary, preferences: UserPreferences) -> List[str]:
        """시간 배분 검토"""
        issues = []
        
        for day in itinerary.days:
            # 1. 하루 이동 시간 계산
            total_travel_time = sum(transfer.travel_min for transfer in day.transfers)
            
            # 2. 체류 시간 계산
            total_stay_time = sum(place.est_stay_min for place in day.morning + day.afternoon + day.evening)
            
            # 3. 총 활동 시간
            total_activity_time = total_travel_time + total_stay_time
            
            # 4. 여행 스타일에 따른 시간 제한
            if preferences.pace == "relaxed" and total_activity_time > 480:  # 8시간
                issues.append(f"{day.date}: 여유로운 여행에 비해 너무 많은 활동이 계획되어 있습니다")
            elif preferences.pace == "packed" and total_activity_time < 360:  # 6시간
                issues.append(f"{day.date}: 빡빡한 여행에 비해 활동이 부족합니다")
            elif preferences.pace == "balanced" and total_activity_time > 600:  # 10시간
                issues.append(f"{day.date}: 균형잡힌 여행에 비해 너무 많은 활동이 계획되어 있습니다")
            
            # 5. 식사 시간 고려
            if not day.lunch and not day.dinner:
                issues.append(f"{day.date}: 식사 시간이 계획되지 않았습니다")
        
        return issues
    
    def _review_efficiency(self, itinerary: Itinerary) -> List[str]:
        """이동 효율성 검토"""
        issues = []
        
        for day in itinerary.days:
            places = day.morning + day.afternoon + day.evening
            
            if len(places) < 2:
                continue
            
            # 1. 이동 거리 최적화 확인
            total_distance = sum(transfer.distance_km for transfer in day.transfers)
            
            if total_distance > 20:  # 20km 이상
                issues.append(f"{day.date}: 하루 이동 거리가 너무 깁니다 ({total_distance:.1f}km)")
            
            # 2. 이동 시간 최적화 확인
            total_travel_time = sum(transfer.travel_min for transfer in day.transfers)
            
            if total_travel_time > 180:  # 3시간 이상
                issues.append(f"{day.date}: 하루 이동 시간이 너무 깁니다 ({total_travel_time}분)")
            
            # 3. 교통수단 다양성 확인
            transport_modes = set(transfer.mode for transfer in day.transfers)
            if len(transport_modes) == 1 and "walk" in transport_modes and total_distance > 10:
                issues.append(f"{day.date}: 도보만으로는 너무 먼 거리를 이동합니다")
        
        return issues
    
    def _review_preference_alignment(self, itinerary: Itinerary, preferences: UserPreferences) -> List[str]:
        """사용자 선호도 일치성 검토"""
        issues = []
        
        # 1. 관심사 반영 확인
        all_place_categories = set()
        for day in itinerary.days:
            for place in day.morning + day.afternoon + day.evening:
                all_place_categories.add(place.category)
        
        # 사용자 관심사와 장소 카테고리 매칭
        interest_category_map = {
            "역사": ["landmark", "museum", "historic"],
            "예술": ["museum", "gallery", "theater"],
            "자연": ["park", "garden", "nature"],
            "음식": ["restaurant", "cafe", "market"],
            "쇼핑": ["shopping", "market", "mall"],
            "액티비티": ["park", "sports", "adventure"]
        }
        
        covered_interests = []
        for interest in preferences.interests:
            if any(cat in all_place_categories for cat in interest_category_map.get(interest, [])):
                covered_interests.append(interest)
        
        if len(covered_interests) < len(preferences.interests) * 0.7:  # 70% 이상 커버
            missing_interests = set(preferences.interests) - set(covered_interests)
            issues.append(f"사용자 관심사가 충분히 반영되지 않았습니다: {', '.join(missing_interests)}")
        
        # 2. 예산 수준 확인
        if preferences.budget_level == "low":
            expensive_places = [p for day in itinerary.days for p in day.morning + day.afternoon + day.evening 
                              if p.price_level and p.price_level >= 4]
            if expensive_places:
                issues.append("저예산 여행에 비해 고가의 장소가 포함되어 있습니다")
        
        # 3. 여행 인원 고려
        if preferences.party > 4:
            # 대규모 그룹을 위한 장소 선택 확인
            small_places = [p for day in itinerary.days for p in day.morning + day.afternoon + day.evening 
                          if "small" in p.description.lower() if p.description]
            if small_places:
                issues.append("대규모 그룹에 비해 좁은 장소가 포함되어 있습니다")
        
        return issues
    
    def _calculate_overall_score(self, basic_issues: List[str], time_issues: List[str], 
                                efficiency_issues: List[str], preference_issues: List[str]) -> float:
        """종합 점수 계산"""
        # 기본 점수: 10점
        base_score = 10.0
        
        # 각 카테고리별 감점
        basic_deduction = min(len(basic_issues) * 2.0, 4.0)  # 최대 4점 감점
        time_deduction = min(len(time_issues) * 1.5, 3.0)    # 최대 3점 감점
        efficiency_deduction = min(len(efficiency_issues) * 1.0, 2.0)  # 최대 2점 감점
        preference_deduction = min(len(preference_issues) * 1.0, 2.0)  # 최대 2점 감점
        
        total_deduction = basic_deduction + time_deduction + efficiency_deduction + preference_deduction
        
        final_score = max(base_score - total_deduction, 0.0)
        return round(final_score, 1)
    
    def _generate_improvement_suggestions(self, basic_issues: List[str], time_issues: List[str],
                                        efficiency_issues: List[str], preference_issues: List[str]) -> List[str]:
        """개선 제안 생성"""
        suggestions = []
        
        # 기본 요구사항 개선
        if any("중복 방문" in issue for issue in basic_issues):
            suggestions.append("중복 방문하는 장소를 제거하거나 다른 장소로 대체하세요")
        
        if any("식사 시간" in issue for issue in time_issues):
            suggestions.append("각 날짜에 점심과 저녁 식사 시간을 포함하세요")
        
        if any("이동 거리" in issue for issue in efficiency_issues):
            suggestions.append("하루 이동 거리를 줄이거나 교통수단을 다양화하세요")
        
        if any("관심사" in issue for issue in preference_issues):
            suggestions.append("사용자 관심사에 더 적합한 장소를 추가하세요")
        
        if any("예산" in issue for issue in preference_issues):
            suggestions.append("예산 수준에 맞는 장소를 선택하세요")
        
        # 일반적인 개선 제안
        if len(basic_issues + time_issues + efficiency_issues + preference_issues) > 5:
            suggestions.append("전체적으로 계획을 단순화하고 여유 시간을 추가하세요")
        
        if not suggestions:
            suggestions.append("현재 계획이 양호합니다. 세부 조정만 필요할 수 있습니다")
        
        return suggestions

# 기존 함수 유지 (하위 호환성)
def validate_plans(days: list[DayPlan]) -> list[str]:
    """기존 함수 유지"""
    issues = []
    seen = set()
    for d in days:
        for p in d.morning + d.afternoon + d.evening:
            if p.name in seen:
                issues.append(f"Duplicate place: {p.name} on {d.date}")
            seen.add(p.name)
        total_walk = sum(t.travel_min for t in d.transfers)
        if total_walk > 120:
            issues.append(f"Long walking time ({total_walk} min) on {d.date}")
    return issues
