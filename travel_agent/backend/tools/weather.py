from __future__ import annotations
from ..config import settings

async def get_daily_weather(lat: float, lon: float, date: str) -> dict:
    if not settings.OPENWEATHER_API_KEY:
        return {"date": date, "summary": "(demo) mild, chance of clouds", "temp_c": 20}
    return {"date": date, "summary": "sunny", "temp_c": 24}
