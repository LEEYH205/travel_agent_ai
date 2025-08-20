from __future__ import annotations
from .schemas import UserPreferences, Itinerary, PlanResponse
from .agents.researcher import run_research
from .agents.attractions import select_attractions
from .agents.planner import plan_days
from .agents.local_guide import get_local_tips
from .agents.critic import validate_plans

async def plan_itinerary(pref: UserPreferences) -> PlanResponse:
    _ = await run_research(pref)
    places = await select_attractions(pref.destination, pref.interests)
    if not places:
        raise ValueError("No candidate places")
    days = plan_days(pref, places)
    issues = validate_plans(days)
    summary = f"{pref.destination} {pref.start_date}~{pref.end_date}, 관심사: {', '.join(pref.interests) or '일반'}"
    if issues:
        summary += "\n주의사항: " + "; ".join(issues)
    tips = get_local_tips(pref.locale)
    itinerary = Itinerary(summary=summary, days=days, tips=tips)
    return PlanResponse(itinerary=itinerary)
