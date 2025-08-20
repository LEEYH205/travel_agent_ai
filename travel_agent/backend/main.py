from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from .schemas import UserPreferences, PlanResponse
from .graph import plan_itinerary
from .orchestrators.crew import plan_with_crew

app = FastAPI(title="Agent Travel Planner")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/plan", response_model=PlanResponse)
async def plan(pref: UserPreferences, mode: str = Query("graph", enum=["graph","crew"])):
    try:
        if mode == "crew":
            return await plan_with_crew(pref)
        return await plan_itinerary(pref)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
