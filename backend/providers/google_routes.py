"""
Google Routes API with live traffic. Enabled when GOOGLE_MAPS_KEY is set.
Needs a Google Cloud billing account (a payment method), so it is off until you add a key.
UNTESTED: written from memory of the Routes API v2. Run /check-sources after adding a key.
"""
import httpx
from fastapi import HTTPException

import config
from .base import Place, Route, RoutingProvider

URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
FIELDS = ",".join([
    "routes.duration", "routes.staticDuration", "routes.distanceMeters",
    "routes.polyline.geoJsonLinestring", "routes.description",
])


def _secs(value):
    """Google returns durations like '1234s'."""
    return float(str(value).rstrip("s")) if value is not None else None


def _point(p: Place):
    return {"location": {"latLng": {"latitude": p.lat, "longitude": p.lng}}}


class GoogleRouting(RoutingProvider):
    name = "google"
    key_env = "GOOGLE_MAPS_KEY"
    live = True

    @property
    def configured(self):
        return bool(config.GOOGLE_MAPS_KEY)

    async def fetch_routes(self, origin: Place, dest: Place):
        body = {
            "origin": _point(origin), "destination": _point(dest),
            "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE_OPTIMAL",
            "computeAlternativeRoutes": True, "polylineEncoding": "GEO_JSON_LINESTRING",
        }
        headers = {"X-Goog-Api-Key": config.GOOGLE_MAPS_KEY, "X-Goog-FieldMask": FIELDS}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(URL, json=body, headers=headers)
        except httpx.RequestError as exc:
            raise HTTPException(502, f"Could not reach Google: {exc.__class__.__name__}")

        if resp.status_code in (400, 401, 403):
            raise HTTPException(502, f"Google rejected the request ({resp.status_code}). Check key, billing, and that Routes API is enabled.")
        if resp.status_code == 429:
            raise HTTPException(502, "Google quota reached.")
        if resp.status_code >= 400:
            raise HTTPException(502, f"Google routing failed ({resp.status_code}).")

        routes = []
        for r in resp.json().get("routes") or []:
            duration = _secs(r.get("duration"))
            static = _secs(r.get("staticDuration")) or duration
            line = ((r.get("polyline") or {}).get("geoJsonLinestring") or {}).get("coordinates") or []
            desc = (r.get("description") or "").strip()
            roads = [desc[4:] if desc.lower().startswith("via ") else desc] if desc else []
            routes.append(Route(
                duration_s=duration, distance_m=r.get("distanceMeters", 0), coordinates=line, roads=roads,
                free_flow_s=static, traffic_delay_s=max(0.0, duration - static),
            ))
        if not routes:
            raise HTTPException(404, "No drivable route found between those points.")
        return routes