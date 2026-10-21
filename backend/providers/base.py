"""
Provider interfaces. Everything outside this folder only talks to these shapes,
so any data source can be swapped in without touching the rest of the app.

HOW TO ADD A NEW PROVIDER
1. Copy the closest existing file in this folder (routing: osrm.py, incidents: chp.py,
   geocoding: nominatim.py) and change the HTTP call and the parsing.
   Convert the response into the shapes below (Route, Incident, Place).
2. Register it in the matching dict at the top of providers/__init__.py.
3. Add its key to config.py and .env.example, then put its name in
   ROUTING_ORDER / INCIDENT_SOURCES / GEOCODER_ORDER in .env.
"""
import time
from dataclasses import dataclass, field
from typing import List, Optional

from fastapi import HTTPException


@dataclass
class Place:
    lat: float
    lng: float
    name: str = ""

    def to_dict(self):
        return {"lat": self.lat, "lng": self.lng, "name": self.name}


@dataclass
class Route:
    duration_s: float                       # travel time. Includes live traffic if the provider is live.
    distance_m: float
    coordinates: list                       # [[lng, lat], ...]
    roads: List[str] = field(default_factory=list)  # main roads, longest first
    free_flow_s: Optional[float] = None     # time with no traffic
    historic_s: Optional[float] = None      # typical time for this hour, if known
    traffic_delay_s: Optional[float] = None # delay caused by traffic, if known


@dataclass
class Incident:
    id: str
    kind: str          # accident | closure | construction | hazard | event
    label: str
    delay_minutes: int  # estimated if the source does not publish it
    lat: float
    lng: float
    source: str = ""

    def to_dict(self):
        return {
            "id": self.id, "kind": self.kind, "label": self.label,
            "delayMinutes": self.delay_minutes, "lat": self.lat, "lng": self.lng, "source": self.source,
        }


class Provider:
    name = ""
    key_env = None  # name of the .env variable, used in messages

    @property
    def configured(self):
        return True

    def not_configured_note(self):
        return f"Set {self.key_env} in .env to enable." if self.key_env else "Not configured."

    async def check(self):
        raise NotImplementedError


class RoutingProvider(Provider):
    live = False  # True if duration_s already includes live traffic

    async def fetch_routes(self, origin: Place, dest: Place) -> List[Route]:
        raise NotImplementedError

    async def check(self):
        routes = await self.fetch_routes(Place(37.7749, -122.4194), Place(37.7955, -122.3937))
        return {"ok": True, "routes": len(routes), "live_traffic": self.live}


class Geocoder(Provider):
    async def geocode(self, query: str) -> Place:
        raise NotImplementedError

    async def check(self):
        place = await self.geocode("Ferry Building, San Francisco")
        return {"ok": True, "sample": place.name}


class IncidentProvider(Provider):
    ttl_seconds = 120

    def __init__(self):
        self._at = 0.0
        self._data = None

    async def raw(self) -> list:
        """Unprocessed records, for debugging field names."""
        raise NotImplementedError

    async def _fetch(self) -> List[Incident]:
        raise NotImplementedError

    async def fetch(self) -> List[Incident]:
        """Cached. Never raises, so routes still work when an incident source is down."""
        if self._data is not None and time.monotonic() - self._at < self.ttl_seconds:
            return self._data
        try:
            self._data = await self._fetch()
            self._at = time.monotonic()
            return self._data
        except Exception as exc:  # noqa: BLE001
            print(f"[{self.name}] fetch failed, using {'stale cache' if self._data else 'no incidents'}: {exc}")
            return self._data or []

    async def check(self):
        return {"ok": True, "records": len(await self.raw())}


def http_error(status, message):
    return HTTPException(status, message)