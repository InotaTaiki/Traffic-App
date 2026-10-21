import os

from dotenv import load_dotenv

load_dotenv()  # reads backend/.env if it exists


def _list(name, default):
    return [s.strip().lower() for s in os.getenv(name, default).split(",") if s.strip()]


TOMTOM_KEY = os.getenv("TOMTOM_KEY", "").strip()
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY", "").strip()
API_511_KEY = os.getenv("API_511_KEY", "").strip()

ROUTING_ORDER = _list("ROUTING_ORDER", "google,tomtom,osrm")
GEOCODER_ORDER = _list("GEOCODER_ORDER", "nominatim")
INCIDENT_SOURCES = _list("INCIDENT_SOURCES", "chp,511")

USER_AGENT = os.getenv("USER_AGENT", "traffic-app-dev").strip() or "traffic-app-dev"
LOG_ENABLED = os.getenv("LOG_ENABLED", "false").lower() == "true"
LOG_INTERVAL_MIN = int(os.getenv("LOG_INTERVAL_MIN", "15"))
DB_PATH = os.getenv("DB_PATH", "./data/traffic.db")