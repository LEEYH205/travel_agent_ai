from __future__ import annotations
from geopy.geocoders import Nominatim

_geocoder = Nominatim(user_agent="travel_agent")

def geocode_city(city: str) -> tuple[float, float] | None:
    try:
        loc = _geocoder.geocode(city)
        if not loc:
            return None
        return (loc.latitude, loc.longitude)
    except Exception:
        return None
