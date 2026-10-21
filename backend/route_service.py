import asyncio
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException

import providers
from geo import distance_to_polyline_m

INCIDENT_RADIUS_M = 150
W_PER_INCIDENT = 0.5  # small tie-breaker toward routes with fewer incidents
LA = ZoneInfo("America/Los_Angeles")
MODES = providers.MODES
MODE_WORDS = {"car": "driving", "walk": "walking", "bike": "cycling"}


def incidents_on_route(route, incidents):
    return [i for i in incidents if distance_to_polyline_m(i.lat, i.lng, route.coordinates) <= INCIDENT_RADIUS_M]


def _arrival(eta_min):
    t = datetime.now(LA) + timedelta(minutes=eta_min)
    return t.strftime("%I:%M %p").lstrip("0")


def _traffic_from_delay_ratio(delay_s, free_flow_s):
    ratio = delay_s / free_flow_s if free_flow_s else 0
    return "heavy" if ratio >= 0.35 else "slow" if ratio >= 0.12 else "clear"


def _traffic_from_incidents(delay_min):
    return "heavy" if delay_min >= 10 else "slow" if delay_min >= 3 else "clear"


def _unique_name(roads, i, used):
    """'Via A', else 'Via A and B', else 'Via A (Alt 2)', so alternatives never share a name."""
    if not roads:
        candidates = [f"Route {i + 1}"]
    else:
        candidates = [f"Via {roads[0]}"]
        if len(roads) > 1:
            candidates.append(f"Via {roads[0]} and {roads[1]}")
        candidates.append(f"{candidates[0]} (Alt {i + 1})")
    for c in candidates:
        if c not in used:
            used.add(c)
            return c
    used.add(candidates[-1])
    return candidates[-1]


def _straight_line_miles(a, b):
    """Great-circle distance, so the app can say how far away a place is."""
    r = 3958.8
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b.lng - a.lng) / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(h)), 1)


def _source_label(provider, mode):
    if mode == "car":
        sources = ", ".join(p.name for p in providers.active("incidents")) or "none"
        kind = "live traffic" if provider.live else "free-flow, no live speeds"
        return f"routing: {provider.name} ({kind}); incidents: {sources}"
    return f"routing: {provider.name} ({MODE_WORDS[mode]}, no live data)"


def _options(routes, provider, mode, incidents):
    """Turns provider routes into the app's route options, best first."""
    built, used_names = [], set()
    for i, r in enumerate(routes):
        free_flow_s = r.free_flow_s or r.duration_s

        if mode == "car":
            nearby = incidents_on_route(r, incidents)
            incident_delay = sum(n.delay_minutes for n in nearby)
            # Live providers already include traffic in the ETA. Otherwise add estimated incident delay.
            eta = round(r.duration_s / 60) if provider.live else round(free_flow_s / 60 + incident_delay)
            if r.traffic_delay_s is not None:
                traffic = _traffic_from_delay_ratio(r.traffic_delay_s, free_flow_s)
            else:
                traffic = _traffic_from_incidents(incident_delay)
            variable = bool(nearby) or (r.historic_s is not None and r.duration_s > r.historic_s * 1.25)
        else:
            # Road incidents and traffic do not apply to walking or cycling.
            nearby, traffic, variable = [], "clear", False
            eta = round(r.duration_s / 60)

        option = {
            "id": f"{mode}-{i + 1}",
            "name": _unique_name(r.roads, i, used_names),
            "etaMinutes": eta,
            "freeFlowMinutes": round(free_flow_s / 60),
            "distanceMiles": round(r.distance_m / 1609.344, 1),
            "arrivalTime": _arrival(eta),
            "traffic": traffic,
            "reliability": "variable" if variable else "steady",
            "incidents": [n.to_dict() for n in nearby],
            "geometry": r.coordinates,
        }
        built.append((eta + W_PER_INCIDENT * len(nearby), option))

    built.sort(key=lambda b: (b[0], b[1]["distanceMiles"]))
    max_eta = max(o["etaMinutes"] for _, o in built)
    out = []
    for _, o in built:
        saved = max_eta - o["etaMinutes"]
        if saved > 0:
            o["minutesSaved"] = saved
        out.append(o)
    return out


async def _mode_result(origin, dest, mode, incidents):
    routes, provider = await providers.find_routes(origin, dest, mode)
    return {"trafficSource": _source_label(provider, mode), "routes": _options(routes, provider, mode, incidents)}


async def get_routes(from_query, to_query, mode="car"):
    """Routes for one travel mode."""
    origin = await providers.geocode(from_query)
    dest = await providers.geocode(to_query)
    incidents = await providers.fetch_incidents() if mode == "car" else []
    result = await _mode_result(origin, dest, mode, incidents)
    return {
        "generatedAt": datetime.now(LA).isoformat(),
        "mode": mode,
        "origin": origin.to_dict(),
        "destination": dest.to_dict(),
        **result,
    }


async def get_trips(from_query, to_query):
    """Routes for every travel mode at once, so the app can offer car, walk, and bike."""
    # Geocoding runs one at a time on purpose (free geocoders allow 1 request/second).
    origin = await providers.geocode(from_query)
    dest = await providers.geocode(to_query)
    incidents = await providers.fetch_incidents()

    results = await asyncio.gather(
        *(_mode_result(origin, dest, m, incidents) for m in MODES), return_exceptions=True
    )
    modes = {}
    for m, res in zip(MODES, results):
        if isinstance(res, HTTPException):
            modes[m] = {"ok": False, "error": res.detail}
        elif isinstance(res, Exception):
            modes[m] = {"ok": False, "error": f"Could not find a {MODE_WORDS[m]} route."}
        else:
            modes[m] = {"ok": True, **res}

    return {
        "generatedAt": datetime.now(LA).isoformat(),
        "straightLineMiles": _straight_line_miles(origin, dest),
        "origin": origin.to_dict(),
        "destination": dest.to_dict(),
        "modes": modes,
    }