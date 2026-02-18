"""Configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Laravel API
    API_URL: str = os.getenv("ARCHGEE_API_URL", "http://localhost")
    API_TOKEN: str = os.getenv("ARCHGEE_API_TOKEN", "")

    # Adzuna
    ADZUNA_APP_ID: str = os.getenv("ADZUNA_APP_ID", "")
    ADZUNA_APP_KEY: str = os.getenv("ADZUNA_APP_KEY", "")

    # CareerJet
    CAREERJET_AFFID: str = os.getenv("CAREERJET_AFFID", "")

    # Jooble
    JOOBLE_API_KEY: str = os.getenv("JOOBLE_API_KEY", "")

    # Scheduling
    FETCH_INTERVAL_HOURS: int = int(os.getenv("FETCH_INTERVAL_HOURS", "6"))
    MAX_JOBS_PER_FETCH: int = int(os.getenv("MAX_JOBS_PER_FETCH", "100"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()
