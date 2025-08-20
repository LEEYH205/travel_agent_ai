from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional

class UserPreferences(BaseModel):
    destination: str = Field(..., description="City or region, e.g., 'Paris'")
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    interests: List[str] = Field(default_factory=list)
    pace: str = Field(default="balanced", description="relaxed | balanced | packed")
    budget_level: str = Field(default="mid", description="low | mid | high")
    party: int = Field(default=1)
    locale: str = Field(default="ko_KR")

class Place(BaseModel):
    name: str
    category: str = "poi"
    lat: float
    lon: float
    description: Optional[str] = None
    url: Optional[str] = None
    est_stay_min: int = 60

class Leg(BaseModel):
    from_place: str
    to_place: str
    travel_min: int
    distance_km: float
    mode: str = "walk"

class DayPlan(BaseModel):
    date: str
    morning: List[Place]
    lunch: Optional[str] = None
    afternoon: List[Place]
    dinner: Optional[str] = None
    evening: List[Place]
    transfers: List[Leg] = Field(default_factory=list)

class Tips(BaseModel):
    etiquette: List[str] = Field(default_factory=list)
    packing: List[str] = Field(default_factory=list)
    safety: List[str] = Field(default_factory=list)

class Itinerary(BaseModel):
    summary: str
    days: List[DayPlan]
    tips: Tips

class PlanResponse(BaseModel):
    itinerary: Itinerary
