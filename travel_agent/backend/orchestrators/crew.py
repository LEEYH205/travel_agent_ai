from __future__ import annotations
import os
import json
import asyncio
from typing import Dict, Any, List
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from crewai.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

from ..schemas import UserPreferences, PlanResponse, Itinerary, DayPlan, Place, Tips
from ..agents import ResearchAgent, AttractionsAgent, ItineraryPlannerAgent, LocalGuideAgent
from ..tools.places import search_places_async
from ..tools.weather import get_forecast_weather
from ..tools.directions import get_directions_async, optimize_route_async
from ..tools.wiki import get_destination_info

load_dotenv()

class EnhancedCrewOrchestrator:
    """향상된 CrewAI 기반 여행 계획 오케스트레이터"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.tavily_tool = self._initialize_tavily()
        self.agents = self._initialize_agents()
        
    def _initialize_llm(self):
        """LLM 초기화"""
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.4, 
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def _initialize_tavily(self):
        """Tavily 검색 도구 초기화"""
        key = os.getenv("TAVILY_API_KEY")
        return TavilySearchResults(api_key=key, max_results=5) if key else None
    
    def _initialize_agents(self):
        """CrewAI Agent들 초기화"""
        agents = {}
        
        # 1. Destination Researcher Agent
        agents['researcher'] = Agent(
            role="Travel Destination Research Specialist",
            goal="여행지의 최신 정보, 날씨, 시즌별 특이사항, 축제, 이벤트를 종합적으로 수집하고 분석합니다",
            backstory="""당신은 여행 전문 연구원입니다. 
            세계 각지의 여행지에 대한 깊이 있는 지식을 가지고 있으며, 
            날씨, 문화, 축제, 시즌별 특이사항 등을 종합적으로 분석하여 
            여행 계획에 필요한 핵심 정보를 제공합니다.""",
            tools=[self._web_search_tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        # 2. Attractions Specialist Agent
        agents['attractions'] = Agent(
            role="Attractions & Places Specialist",
            goal="사용자의 관심사, 여행 스타일, 예산에 맞는 최적의 관광명소를 선별하고 추천합니다",
            backstory="""당신은 여행지의 관광명소 전문가입니다. 
            각 지역의 숨겨진 명소부터 대표적인 관광지를 모두 알고 있으며, 
            사용자의 취향과 여행 스타일에 맞는 맞춤형 추천을 제공합니다.
            문화, 역사, 자연, 엔터테인먼트 등 다양한 카테고리의 명소를 
            균형있게 조합하여 완벽한 여행 경험을 만들어냅니다.""",
            tools=[self._search_places_tool, self._web_search_tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        # 3. Itinerary Planner Agent
        agents['planner'] = Agent(
            role="Itinerary Planning Expert",
            goal="사용자의 여행 스타일, 시간, 이동 거리를 고려하여 최적의 일별 여행 계획을 수립합니다",
            backstory="""당신은 여행 일정 계획의 전문가입니다. 
            각 관광지의 특성, 이동 시간, 운영 시간, 사용자 선호도를 종합적으로 분석하여 
            효율적이고 만족도 높은 여행 일정을 만들어냅니다.
            하루의 흐름을 자연스럽게 연결하고, 피로도를 최소화하면서 
            최대한 많은 경험을 할 수 있도록 계획합니다.""",
            tools=[self._calculate_route_tool, self._optimize_route_tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        # 4. Local Guide Agent
        agents['local_guide'] = Agent(
            role="Local Culture & Travel Guide",
            goal="현지 문화, 관습, 주의사항, 추천 준비물을 제공하여 안전하고 즐거운 여행을 도와줍니다",
            backstory="""당신은 현지 문화와 여행에 정통한 가이드입니다. 
            각 지역의 문화적 특성, 관습, 주의사항을 잘 알고 있으며, 
            실용적이고 구체적인 여행 팁을 제공합니다.
            안전하고 문화적으로 존중받는 여행을 위한 가이드 역할을 합니다.""",
            tools=[self._web_search_tool, self._get_local_info_tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        return agents
    
    @tool
    def _web_search_tool(self, query: str) -> str:
        """최신 웹 검색을 통한 정보 수집 (이벤트, 축제, 시즌별 특이사항 등)"""
        try:
            if not self.tavily_tool:
                return "검색 도구를 사용할 수 없습니다: TAVILY_API_KEY가 설정되지 않았습니다."
            
            results = self.tavily_tool.invoke(query)
            return str(results)
        except Exception as e:
            return f"검색 중 오류 발생: {e}"
    
    @tool
    def _search_places_tool(self, payload: dict) -> str:
        """사용자 관심사와 선호도에 맞는 관광명소 검색 및 추천"""
        try:
            destination = payload.get("destination", "")
            interests = payload.get("interests", [])
            
            if not destination or not interests:
                return "목적지와 관심사 정보가 필요합니다."
            
            # 비동기 함수를 동기적으로 실행
            loop = asyncio.get_event_loop()
            places = loop.run_until_complete(
                search_places_async(destination, interests, limit=15)
            )
            
            # Place 객체를 딕셔너리로 변환
            places_data = []
            for place in places:
                places_data.append({
                    "name": place.name,
                    "category": place.category,
                    "lat": place.lat,
                    "lon": place.lon,
                    "description": place.description,
                    "est_stay_min": place.est_stay_min,
                    "rating": getattr(place, 'rating', 0),
                    "price_level": getattr(place, 'price_level', 0)
                })
            
            return json.dumps(places_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return f"장소 검색 중 오류 발생: {e}"
    
    @tool
    def _calculate_route_tool(self, payload: dict) -> str:
        """두 지점 간의 경로 계산 및 이동 시간 제공"""
        try:
            origin = payload.get("origin")
            destination = payload.get("destination")
            mode = payload.get("mode", "walking")
            
            if not origin or not destination:
                return "출발지와 목적지 정보가 필요합니다."
            
            # 비동기 함수를 동기적으로 실행
            loop = asyncio.get_event_loop()
            route = loop.run_until_complete(
                get_directions_async(
                    (origin["lat"], origin["lon"]),
                    (destination["lat"], destination["lon"]),
                    mode
                )
            )
            
            if route:
                return json.dumps(route, ensure_ascii=False, indent=2)
            else:
                return "경로를 계산할 수 없습니다."
                
        except Exception as e:
            return f"경로 계산 중 오류 발생: {e}"
    
    @tool
    def _optimize_route_tool(self, payload: dict) -> str:
        """여러 장소를 방문하는 최적 경로 계산"""
        try:
            places = payload.get("places", [])
            mode = payload.get("mode", "walking")
            
            if len(places) < 2:
                return "최적화할 장소가 부족합니다 (최소 2개 필요)."
            
            # 장소 리스트를 (이름, 위도, 경도) 튜플로 변환
            places_tuples = []
            for place in places:
                places_tuples.append((place["name"], place["lat"], place["lon"]))
            
            # 비동기 함수를 동기적으로 실행
            loop = asyncio.get_event_loop()
            optimized_places, routes = loop.run_until_complete(
                optimize_route_async(places_tuples, mode)
            )
            
            result = {
                "optimized_places": [
                    {"name": p[0], "lat": p[1], "lon": p[2]} 
                    for p in optimized_places
                ],
                "routes": routes
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return f"경로 최적화 중 오류 발생: {e}"
    
    @tool
    def _get_local_info_tool(self, payload: dict) -> str:
        """여행지의 현지 정보, 문화, 주의사항 수집"""
        try:
            destination = payload.get("destination", "")
            if not destination:
                return "목적지 정보가 필요합니다."
            
            # 비동기 함수를 동기적으로 실행
            loop = asyncio.get_event_loop()
            info = loop.run_until_complete(
                get_destination_info(destination, "ko")
            )
            
            if info:
                # 핵심 정보만 추출
                local_info = {
                    "title": info.get("title", ""),
                    "summary": info.get("summary", "")[:500] + "..." if len(info.get("summary", "")) > 500 else info.get("summary", ""),
                    "cultural_info": info.get("cultural_info", {}),
                    "practical_info": info.get("practical_info", {}),
                    "travel_tips": info.get("travel_tips", [])
                }
                return json.dumps(local_info, ensure_ascii=False, indent=2)
            else:
                return "현지 정보를 찾을 수 없습니다."
                
        except Exception as e:
            return f"현지 정보 수집 중 오류 발생: {e}"
    
    def create_tasks(self, preferences: UserPreferences) -> List[Task]:
        """사용자 선호도에 따른 작업 정의"""
        tasks = []
        
        # 1. 여행지 정보 수집 작업
        research_task = Task(
            description=(
                f"'{preferences.destination}'의 여행 정보를 종합적으로 조사하세요.\n"
                f"여행 기간: {preferences.start_date} ~ {preferences.end_date}\n"
                f"관심사: {', '.join(preferences.interests) if preferences.interests else '일반 관광'}\n\n"
                "다음 정보를 포함하여 마크다운 형식으로 작성하세요:\n"
                "• 시즌별 특이사항 및 날씨 정보\n"
                "• 주요 축제 및 이벤트\n"
                "• 여행 주의사항 및 권고사항\n"
                "• 최적 여행 시기\n"
                "• 현지 문화적 특성"
            ),
            agent=self.agents['researcher'],
            expected_output="markdown"
        )
        tasks.append(research_task)
        
        # 2. 관광명소 선별 작업
        attractions_task = Task(
            description=(
                f"'{preferences.destination}'에서 다음 조건에 맞는 관광명소를 선별하세요:\n"
                f"• 관심사: {', '.join(preferences.interests) if preferences.interests else '일반 관광'}\n"
                f"• 여행 스타일: {preferences.pace}\n"
                f"• 예산 수준: {preferences.budget_level}\n"
                f"• 인원: {preferences.party}명\n\n"
                "다음 형식의 JSON 배열로 반환하세요:\n"
                "```json\n"
                "[\n"
                "  {\n"
                "    \"name\": \"장소명\",\n"
                "    \"category\": \"카테고리\",\n"
                "    \"lat\": 위도,\n"
                "    \"lon\": 경도,\n"
                "    \"description\": \"설명\",\n"
                "    \"est_stay_min\": 체류시간(분),\n"
                "    \"rating\": 평점,\n"
                "    \"price_level\": 가격수준\n"
                "  }\n"
                "]\n"
                "```\n"
                "총 8-15개의 다양한 카테고리 명소를 추천하세요."
            ),
            agent=self.agents['attractions'],
            expected_output="json"
        )
        tasks.append(attractions_task)
        
        # 3. 일정 계획 수립 작업
        planning_task = Task(
            description=(
                f"제공된 관광명소를 바탕으로 '{preferences.destination}'의 상세한 여행 일정을 계획하세요.\n"
                f"여행 기간: {preferences.start_date} ~ {preferences.end_date}\n"
                f"여행 스타일: {preferences.pace}\n\n"
                "다음 형식의 JSON으로 반환하세요:\n"
                "```json\n"
                "{\n"
                "  \"days\": [\n"
                "    {\n"
                "      \"date\": \"YYYY-MM-DD\",\n"
                "      \"morning\": [\"장소명1\", \"장소명2\"],\n"
                "      \"lunch\": \"점심 장소 또는 추천\",\n"
                "      \"afternoon\": [\"장소명3\", \"장소명4\"],\n"
                "      \"dinner\": \"저녁 장소 또는 추천\",\n"
                "      \"evening\": [\"장소명5\"],\n"
                "      \"transfers\": [\n"
                "        {\n"
                "          \"from\": \"출발지\",\n"
                "          \"to\": \"도착지\",\n"
                "          \"mode\": \"교통수단\",\n"
                "          \"time\": \"이동시간(분)\",\n"
                "          \"distance\": \"거리(km)\"\n"
                "        }\n"
                "      ]\n"
                "    }\n"
                "  ]\n"
                "}\n"
                "```\n"
                "여행 스타일에 맞게 하루 방문 명소 수를 조절하고, 이동 시간과 거리를 최적화하세요."
            ),
            agent=self.agents['planner'],
            expected_output="json"
        )
        tasks.append(planning_task)
        
        # 4. 현지 가이드 정보 작업
        guide_task = Task(
            description=(
                f"'{preferences.destination}' 방문을 위한 현지 가이드 정보를 제공하세요.\n\n"
                "다음 형식의 마크다운으로 작성하세요:\n"
                "## 🎭 문화 및 예의\n"
                "• 현지 문화적 특성\n"
                "• 주의해야 할 예의\n"
                "• 문화적 금기사항\n\n"
                "## 🎒 준비물\n"
                "• 필수 준비물\n"
                "• 계절별 준비물\n"
                "• 특별 준비물\n\n"
                "## ⚠️ 안전 및 주의사항\n"
                "• 일반적인 주의사항\n"
                "• 특별 주의사항\n"
                "• 긴급연락처\n\n"
                "## 💡 현지 팁\n"
                "• 현지인만 아는 팁\n"
                "• 절약 팁\n"
                "• 특별한 경험 팁"
            ),
            agent=self.agents['local_guide'],
            expected_output="markdown"
        )
        tasks.append(guide_task)
        
        return tasks
    
    async def plan_with_crew(self, preferences: UserPreferences) -> PlanResponse:
        """CrewAI를 사용한 여행 계획 수립"""
        try:
            # 작업 정의
            tasks = self.create_tasks(preferences)
            
            # Crew 생성 및 실행
            crew = Crew(
                agents=list(self.agents.values()),
                tasks=tasks,
                verbose=True,
                memory=True
            )
            
            # 작업 실행
            result = crew.kickoff()
            
            # 결과 파싱 및 처리
            processed_result = await self._process_crew_result(result, preferences)
            
            return processed_result
            
        except Exception as e:
            logger.error(f"CrewAI 실행 중 오류: {e}")
            # 오류 발생 시 폴백 방식으로 처리
            return await self._fallback_planning(preferences)
    
    async def _process_crew_result(self, result: Any, preferences: UserPreferences) -> PlanResponse:
        """CrewAI 결과 파싱 및 처리"""
        try:
            # 결과에서 일정 정보 추출
            itinerary_data = self._extract_itinerary_from_result(result)
            
            if itinerary_data and itinerary_data.get("days"):
                # CrewAI 결과를 사용하여 일정 생성
                days = self._create_day_plans_from_crew_result(itinerary_data["days"], preferences)
            else:
                # 기본 일정 생성
                days = await self._create_basic_itinerary(preferences)
            
            # 현지 가이드 정보 추출
            tips = self._extract_tips_from_result(result)
            
            # 요약 생성
            summary = f"{preferences.destination} {preferences.start_date}~{preferences.end_date}, 관심사: {', '.join(preferences.interests) or '일반'}"
            
            return PlanResponse(
                itinerary=Itinerary(
                    summary=summary,
                    days=days,
                    tips=tips
                )
            )
            
        except Exception as e:
            logger.error(f"결과 처리 중 오류: {e}")
            return await self._fallback_planning(preferences)
    
    def _extract_itinerary_from_result(self, result: Any) -> Dict[str, Any]:
        """CrewAI 결과에서 일정 정보 추출"""
        try:
            result_str = str(result)
            
            # JSON 형식의 일정 정보 찾기
            start = result_str.find("{")
            end = result_str.rfind("}") + 1
            
            if start != -1 and end != -1:
                json_str = result_str[start:end]
                return json.loads(json_str)
            
            return {}
            
        except Exception as e:
            logger.error(f"일정 정보 추출 중 오류: {e}")
            return {}
    
    def _create_day_plans_from_crew_result(self, crew_days: List[Dict], preferences: UserPreferences) -> List[DayPlan]:
        """CrewAI 결과를 바탕으로 DayPlan 생성"""
        days = []
        
        try:
            for crew_day in crew_days:
                # 장소 이름을 Place 객체로 변환
                morning_places = self._get_places_by_names(crew_day.get("morning", []))
                afternoon_places = self._get_places_by_names(crew_day.get("afternoon", []))
                evening_places = self._get_places_by_names(crew_day.get("evening", []))
                
                # 이동 정보 생성
                transfers = []
                if crew_day.get("transfers"):
                    for transfer in crew_day["transfers"]:
                        transfers.append({
                            "from_place": transfer.get("from", ""),
                            "to_place": transfer.get("to", ""),
                            "travel_min": int(transfer.get("time", 0)),
                            "distance_km": float(transfer.get("distance", 0)),
                            "mode": transfer.get("mode", "walk")
                        })
                
                day_plan = DayPlan(
                    date=crew_day.get("date", ""),
                    morning=morning_places,
                    lunch=crew_day.get("lunch"),
                    afternoon=afternoon_places,
                    dinner=crew_day.get("dinner"),
                    evening=evening_places,
                    transfers=transfers
                )
                
                days.append(day_plan)
                
        except Exception as e:
            logger.error(f"CrewAI 결과 기반 일정 생성 중 오류: {e}")
        
        return days
    
    def _get_places_by_names(self, place_names: List[str]) -> List[Place]:
        """장소 이름 리스트를 Place 객체 리스트로 변환"""
        places = []
        
        for name in place_names:
            # 간단한 Place 객체 생성 (실제 구현에서는 데이터베이스나 캐시에서 조회)
            place = Place(
                name=name,
                category="poi",
                lat=0.0,  # 실제 구현에서는 위도/경도 조회
                lon=0.0,
                description=f"{name} - 추천 관광지",
                est_stay_min=60
            )
            places.append(place)
        
        return places
    
    def _extract_tips_from_result(self, result: Any) -> Tips:
        """CrewAI 결과에서 현지 가이드 정보 추출"""
        try:
            result_str = str(result)
            
            # 기본 팁
            tips = Tips(
                etiquette=["현지 문화와 관습을 존중하세요"],
                packing=["편한 신발", "보조 배터리", "현지용 유심/ESIM"],
                safety=["소매치기 주의", "늦은 밤 외진 골목 피하기"]
            )
            
            # 결과에서 추가 팁 추출 시도
            # (실제 구현에서는 더 정교한 파싱 로직 필요)
            
            return tips
            
        except Exception as e:
            logger.error(f"팁 추출 중 오류: {e}")
            return Tips(
                etiquette=["현지 문화와 관습을 존중하세요"],
                packing=["편한 신발", "보조 배터리"],
                safety=["일반적인 여행 주의사항 준수"]
            )
    
    async def _create_basic_itinerary(self, preferences: UserPreferences) -> List[DayPlan]:
        """기본 일정 생성 (폴백)"""
        try:
            # 장소 검색
            places = await search_places_async(preferences.destination, preferences.interests, 12)
            
            if not places:
                # 데모 장소 사용
                from ..tools.places import get_candidate_places
                places_data = get_candidate_places(preferences.destination, preferences.interests)
                places = [Place(**place) for place in places_data]
            
            # 기본 일정 계획
            from ..agents.planner import ItineraryPlannerAgent
            planner = ItineraryPlannerAgent()
            days = await planner.plan_days(preferences, places)
            
            return days
            
        except Exception as e:
            logger.error(f"기본 일정 생성 중 오류: {e}")
            return []
    
    async def _fallback_planning(self, preferences: UserPreferences) -> PlanResponse:
        """CrewAI 실패 시 폴백 방식으로 일정 계획"""
        try:
            # 기본 일정 생성
            days = await self._create_basic_itinerary(preferences)
            
            # 기본 팁
            tips = Tips(
                etiquette=["현지 문화와 관습을 존중하세요"],
                packing=["편한 신발", "보조 배터리"],
                safety=["일반적인 여행 주의사항 준수"]
            )
            
            summary = f"{preferences.destination} {preferences.start_date}~{preferences.end_date}, 관심사: {', '.join(preferences.interests) or '일반'}"
            
            return PlanResponse(
                itinerary=Itinerary(
                    summary=summary,
                    days=days,
                    tips=tips
                )
            )
            
        except Exception as e:
            logger.error(f"폴백 계획 수립 중 오류: {e}")
            # 최종 폴백: 빈 일정 반환
            return PlanResponse(
                itinerary=Itinerary(
                    summary=f"{preferences.destination} 여행 계획을 생성할 수 없습니다.",
                    days=[],
                    tips=Tips(
                        etiquette=["기본적인 여행 예의 준수"],
                        packing=["필수 여행용품"],
                        safety=["안전한 여행"]
                    )
                )
            )

# 전역 오케스트레이터 인스턴스
crew_orchestrator = EnhancedCrewOrchestrator()

# 기존 함수와의 호환성을 위한 래퍼
async def plan_with_crew(pref: UserPreferences) -> PlanResponse:
    """기존 코드와의 호환성을 위한 함수"""
    return await crew_orchestrator.plan_with_crew(pref)

# 기존 함수들 (하위 호환성)
def _llm():
    return crew_orchestrator.llm

def _tavily():
    return crew_orchestrator.tavily_tool

@tool
def web_search(q: str) -> str:
    """최신 웹 검색을 통한 정보 수집"""
    return crew_orchestrator._web_search_tool(q)

@tool
def list_places(payload: dict) -> str:
    """사용자 관심사와 선호도에 맞는 관광명소 검색 및 추천"""
    return crew_orchestrator._search_places_tool(payload)

def _greedy_days(pref: UserPreferences, places: list[Place]) -> list[DayPlan]:
    """기존 그리디 알고리즘 기반 일정 계획 (하위 호환성)"""
    from datetime import datetime, timedelta
    start = datetime.fromisoformat(pref.start_date)
    end = datetime.fromisoformat(pref.end_date)
    num_days = (end - start).days + 1
    per_day = max(1, min(4, len(places)//max(1, num_days)))
    
    days: list[DayPlan] = []
    idx = 0
    
    for i in range(num_days):
        picks = places[idx: idx+per_day]
        idx += per_day
        
        transfers = []
        for a, b in zip(picks, picks[1:]):
            from ..tools.directions import haversine_km, estimate_walk_minutes
            km = haversine_km(a.lat, a.lon, b.lat, b.lon)
            transfers.append({
                "from_place": a.name, 
                "to_place": b.name,
                "travel_min": estimate_walk_minutes(km),
                "distance_km": round(km, 2)
            })
        
        days.append(DayPlan(
            date=(start + timedelta(days=i)).date().isoformat(),
            morning=picks[:1], 
            afternoon=picks[1:2], 
            evening=picks[2:],
            lunch=None, 
            dinner=None, 
            transfers=transfers
        ))
    
    return days
