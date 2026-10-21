import asyncio
from datetime import datetime, timezone

import config
from db import insert_log
from backend.providers.incidents511 import fetch_incidents
from mapbox import fetch_routes
from route_service import congestion_shares, incidents_on_route

# Approximate coordinates. Adjust to the corridors you care about.
CORRIDORS = [
    ("marina-to-soma", {"lat": 37.8030, "lng": -122.4360}, {"lat": 37.7785, "lng": -122.3893}),
    ("sunset-to-ferry-building", {"lat": 37.7530, "lng": -122.4940}, {"lat": 37.7955, "lng": -122.3937}),
    ("mission-to-presidio", {"lat": 37.7599, "lng": -122.4148}, {"lat": 37.7989, "lng": -122.4662}),
]


async def tick():
    incidents = await fetch_incidents()
    for name, origin, dest in CORRIDORS:
        try:
            best = (await fetch_routes(origin, dest))[0]  # Mapbox's top route
            heavy, _ = congestion_shares(best)
            insert_log({
                "ts": datetime.now(timezone.utc).isoformat(),
                "corridor": name,
                "duration_s": best["duration"],
                "typical_s": best.get("duration_typical"),
                "distance_m": best["distance"],
                "heavy_share": heavy,
                "incident_count": len(incidents_on_route(best, incidents)),
            })
        except Exception as exc:  # noqa: BLE001
            print(f"[logger] {name} failed: {exc}")
    print(f"[logger] logged {len(CORRIDORS)} corridors at {datetime.now(timezone.utc).isoformat()}")


async def run_logger():
    while True:
        await tick()
        await asyncio.sleep(config.LOG_INTERVAL_MIN * 60)