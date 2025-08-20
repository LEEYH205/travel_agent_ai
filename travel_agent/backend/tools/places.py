from __future__ import annotations
from typing import List, Dict

MOCK_PLACES = [
    {"name":"Central Museum","category":"museum","lat":48.8606,"lon":2.3376,
     "description":"A world-class museum.","est_stay_min":120},
    {"name":"City Cathedral","category":"landmark","lat":48.8530,"lon":2.3499,
     "description":"Historic cathedral.","est_stay_min":60},
    {"name":"Riverside Walk","category":"park","lat":48.857,"lon":2.354,
     "description":"Scenic riverside promenade.","est_stay_min":45}
]

def get_candidate_places(destination: str, interests: list[str]) -> List[Dict]:
    return MOCK_PLACES
