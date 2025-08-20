from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    TAVILY_API_KEY: str | None = os.getenv("TAVILY_API_KEY")

    OPENWEATHER_API_KEY: str | None = os.getenv("OPENWEATHER_API_KEY")
    FOURSQUARE_API_KEY: str | None = os.getenv("FOURSQUARE_API_KEY")
    GOOGLE_MAPS_API_KEY: str | None = os.getenv("GOOGLE_MAPS_API_KEY")
    BING_MAPS_KEY: str | None = os.getenv("BING_MAPS_KEY")

    APP_ENV: str = os.getenv("APP_ENV", "dev")
    DEFAULT_LOCALE: str = os.getenv("DEFAULT_LOCALE", "ko_KR")

settings = Settings()
