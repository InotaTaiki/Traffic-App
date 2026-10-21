"""TomTom Routing API with live traffic. Enabled when TOMTOM_KEY is set."""
import httpx
from fastapi import HTTPException

import config
from .base import Place, Route, RoutingProvider

URL = "https://api.tomtom.com/routing/1/calculateRoute/{lat1},{lng1}:{lat2},{lng2}/json"


def _roads(route):
    instructions = (route.get("guidance") or {}).get("instructions") or []
    total = float(route["summary"]["lengthInMeters"])
    totals = {}
    for i, ins in enumerate(instructions):
        street = (ins.get("street") or "").strip()
        if not street:
            continue
        start = float(ins.get("routeOffsetInMeters", 0))
        end = float(instructions[i + 1].get("routeOffsetInMeters", total)) if i + 1 < len(instructions) else total
        totals[street] = totals.get(street, 0.0) + max(0.0, end - start)
    return [n for n, _ in sorted(totals.items(), key=lambda kv: -kv[1])[:3]]


def normalize(data):
    routes = []
    for r in data.get("routes") or []:
        s = r["summary"]
        routes.append(Route(
            duration_s=s["travelTimeInSeconds"],
            distance_m=s["lengthInMeters"],
            coordinates=[[p["longitude"], p["latitude"]] for leg in r.get("legs", []) for p in leg.get("points", [])],
            roads=_roads(r),
            free_flow_s=s.get("noTrafficTravelTimeInSeconds", s["travelTimeInSeconds"]),
            historic_s=s.get("historicTrafficTravelTimeInSeconds"),
            traffic_delay_s=s.get("trafficDelayInSeconds", 0),
        ))
    return routes


class TomTomRouting(RoutingProvider):
    name = "tomtom"
    key_env = "TOMTOM_KEY"
    live = True

    @property
    def configured(self):
        return bool(config.TOMTOM_KEY)

    async def fetch_routes(self, origin: Place, dest: Place):
        url = URL.format(lat1=origin.lat, lng1=origin.lng, lat2=dest.lat, lng2=dest.lng)
        params = {
            "key": config.TOMTOM_KEY, "traffic": "true", "travelMode": "car", "routeType": "fastest",
            "maxAlternatives": 2, "computeTravelTimeFor": "all", "instructionsType": "text", "language": "en-US",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": config.USER_AGENT}) as client:
                resp = await client.get(url, params=params)
        except httpx.RequestError as exc:
            raise HTTPException(502, f"Could not reach TomTom: {exc.__class__.__name__}")

        if resp.status_code in (401, 403):
            raise HTTPException(502, f"TomTom rejected the key ({resp.status_code}). Check TOMTOM_KEY.")
        if resp.status_code == 429:
            raise HTTPException(502, "TomTom daily limit reached. It resets tomorrow.")
        if resp.status_code >= 400:
            raise HTTPException(502, f"TomTom routing failed ({resp.status_code}).")

        routes = normalize(resp.json())
        if not routes:
            raise HTTPException(404, "No drivable route found between those points.")
        return routes