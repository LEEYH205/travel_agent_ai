from __future__ import annotations
import os, json
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from crewai.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

from ..schemas import UserPreferences, PlanResponse, Itinerary, DayPlan, Place, Tips
from ..tools.places import get_candidate_places
from ..tools.directions import haversine_km, estimate_walk_minutes

load_dotenv()

def _llm():
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                      temperature=0.4, api_key=os.getenv("OPENAI_API_KEY"))

def _tavily():
    key = os.getenv("TAVILY_API_KEY")
    return TavilySearchResults(api_key=key, max_results=5) if key else None

@tool
def web_search(q: str) -> str:
    """Latest web search (events/festivals/season)."""
    try:
        tv = _tavily()
        if not tv:
            return "search_unavailable: no TAVILY_API_KEY"
        return str(tv.invoke(q))
    except Exception as e:
        return f"search_error: {e}"

@tool
def list_places(payload: dict) -> str:
    """Return candidate POIs for destination & interests."""
    dest = payload.get("destination", "")
    interests = payload.get("interests", [])
    rows = get_candidate_places(dest, interests)
    return json.dumps(rows, ensure_ascii=False)

def _greedy_days(pref: UserPreferences, places: list[Place]) -> list[DayPlan]:
    from datetime import datetime, timedelta
    start = datetime.fromisoformat(pref.start_date)
    end = datetime.fromisoformat(pref.end_date)
    num_days = (end - start).days + 1
    per_day = max(1, min(4, len(places)//max(1, num_days)))
    days: list[DayPlan] = []
    idx = 0
    for i in range(num_days):
        picks = places[idx: idx+per_day]; idx += per_day
        transfers = []
        for a, b in zip(picks, picks[1:]):
            km = haversine_km(a.lat, a.lon, b.lat, b.lon)
            transfers.append({"from_place": a.name, "to_place": b.name,
                              "travel_min": estimate_walk_minutes(km),
                              "distance_km": round(km, 2)})
        days.append(DayPlan(
            date=(start + timedelta(days=i)).date().isoformat(),
            morning=picks[:1], afternoon=picks[1:2], evening=picks[2:],
            lunch=None, dinner=None, transfers=transfers
        ))
    return days

async def plan_with_crew(pref: UserPreferences) -> PlanResponse:
    llm = _llm()

    destination_researcher = Agent(
        role="Destination Researcher",
        goal="Find up-to-date info (season, events, advisories) for the trip.",
        backstory="Travel analyst specialized in fresh, accurate, practical facts.",
        tools=[web_search],
        llm=llm, verbose=False,
    )

    attractions_specialist = Agent(
        role="Attractions Specialist",
        goal="Select attractions matched to user interests; avoid duplicates.",
        backstory="Curator focusing on relevance, diversity, and accessibility.",
        tools=[list_places, web_search],
        llm=llm, verbose=False,
    )

    itinerary_planner = Agent(
        role="Itinerary Planner",
        goal="Assemble day-by-day plan minimizing transfers and crowding.",
        backstory="Logistics planner optimizing walking time and cadence.",
        llm=llm, verbose=False,
    )

    local_guide = Agent(
        role="Local Guide",
        goal="Provide localized etiquette, packing tips, safety notes.",
        backstory="Culturally-aware guide with concise, actionable tips.",
        tools=[web_search],
        llm=llm, verbose=False,
    )

    research_task = Task(
        description=(f"Research {pref.destination} for {pref.start_date}~{pref.end_date}. "
                     f"Interests: {', '.join(pref.interests)}. "
                     "Return bullet points for: season/weather, festivals, advisories."),
        agent=destination_researcher, expected_output="markdown"
    )
    attractions_task = Task(
        description=(f"Select 5-12 candidate attractions in {pref.destination} "
                     f"for interests: {', '.join(pref.interests)}. "
                     "Return JSON list with name, category, lat, lon, description, est_stay_min."),
        agent=attractions_specialist, expected_output="json"
    )
    plan_task = Task(
        description=("Create a day-by-day itinerary JSON using given POIs "
                     "with morning/afternoon/evening and logical transfers. "
                     "Limit walking burden; avoid duplicates."),
        agent=itinerary_planner, expected_output="json"
    )
    guide_task = Task(
        description=("Provide concise local tips (etiquette/packing/safety) "
                     "for the locale; max 5 bullets each."),
        agent=local_guide, expected_output="markdown"
    )

    crew = Crew(
        agents=[destination_researcher, attractions_specialist, itinerary_planner, local_guide],
        tasks=[research_task, attractions_task, plan_task, guide_task],
        verbose=False
    )
    result = crew.kickoff()

    # Parse places from the result (best-effort)
    places = []
    try:
        text = str(result)
        start = text.find("["); end = text.rfind("]")+1
        places_raw = json.loads(text[start:end]) if start!=-1 and end!=-1 else []
        for p in places_raw:
            if all(k in p for k in ("name","lat","lon")):
                places.append(Place(
                    name=p["name"], category=p.get("category","poi"),
                    lat=float(p["lat"]), lon=float(p["lon"]),
                    description=p.get("description"),
                    est_stay_min=int(p.get("est_stay_min", 60))
                ))
    except Exception:
        places = []

    if not places:
        rows = get_candidate_places(pref.destination, pref.interests)
        places = [Place(name=r["name"], category=r.get("category","poi"),
                        lat=r["lat"], lon=r["lon"],
                        description=r.get("description"),
                        est_stay_min=r.get("est_stay_min",60)) for r in rows]

    days = _greedy_days(pref, places)
    tips = Tips(etiquette=["현지 예약 문화 준수"], packing=["편한 신발","보조 배터리"], safety=["소매치기 주의"])
    summary = f"{pref.destination} {pref.start_date}~{pref.end_date}, 관심사: {', '.join(pref.interests) or '일반'}"
    return PlanResponse(itinerary=Itinerary(summary=summary, days=days, tips=tips))
