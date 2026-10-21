"""Free OSRM routing for cars, walking, and cycling. No key, no account.

Car uses the public OSRM demo server (free-flow times, no live traffic).
Walking and cycling use the OpenStreetMap community servers, which run a separate OSRM
instance for each profile."""
import httpx
from fastapi import HTTPException

import config
from .base import Place, Route, RoutingProvider

ENDPOINTS = {
    "car": "https://router.project-osrm.org/route/v1/driving/{coords}",
    # These servers use "driving" in the path for every profile. The folder name picks the profile.
    "walk": "https://routing.openstreetmap.de/routed-foot/route/v1/driving/{coords}",
    "bike": "https://routing.openstreetmap.de/routed-bike/route/v1/driving/{coords}",
}
MODE_WORDS = {"car": "driving", "walk": "walking", "bike": "cycling"}


def _top_roads(route):
    totals = {}
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            name = (step.get("name") or "").strip()
            if name:
                totals[name] = totals.get(name, 0.0) + float(step.get("distance", 0.0))
    return [n for n, _ in sorted(totals.items(), key=lambda kv: -kv[1])[:3]]


class OsrmRouting(RoutingProvider):
    name = "osrm"
    live = False
    modes = ("car", "walk", "bike")

    async def fetch_routes(self, origin: Place, dest: Place, mode: str = "car"):
        word = MODE_WORDS[mode]
        coords = f"{origin.lng},{origin.lat};{dest.lng},{dest.lat}"
        try:
            async with httpx.AsyncClient(timeout=20.0, headers={"User-Agent": config.USER_AGENT}) as client:
                resp = await client.get(
                    ENDPOINTS[mode].format(coords=coords),
                    params={"alternatives": "true", "overview": "full", "geometries": "geojson", "steps": "true"},
                )
        except httpx.RequestError as exc:
            raise HTTPException(502, f"Could not reach the {word} routing server: {exc.__class__.__name__}")

        if resp.status_code == 429:
            raise HTTPException(502, f"The {word} routing server is busy. Wait a moment and retry.")
        try:
            data = resp.json()
        except ValueError:
            raise HTTPException(502, f"The {word} routing server returned an unexpected response ({resp.status_code}).")

        code = data.get("code")
        if code in ("NoRoute", "NoSegment"):
            raise HTTPException(404, f"No {word} route found between those points.")
        if code == "TooBig":
            raise HTTPException(400, f"That {word} route is too long for the free routing server.")
        if code != "Ok" or not data.get("routes"):
            raise HTTPException(502, f"{word.capitalize()} routing failed ({code or resp.status_code}).")

        return [
            Route(
                duration_s=r["duration"], distance_m=r["distance"],
                coordinates=r["geometry"]["coordinates"], roads=_top_roads(r),
                free_flow_s=r["duration"],
            )
            for r in data["routes"]
        ]