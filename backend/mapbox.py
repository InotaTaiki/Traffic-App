import httpx
from fastapi import HTTPException

import config
from geo import parse_lat_lng

TIMEOUT = 8.0


def _require_token():
    if not config.MAPBOX_TOKEN:
        raise HTTPException(500, "MAPBOX_TOKEN is not set. Add it to backend/.env and restart.")


def _check(resp, what):
    if resp.status_code in (401, 403):
        raise HTTPException(502, f"Mapbox rejected the token for {what} ({resp.status_code}). Check MAPBOX_TOKEN.")
    if resp.status_code == 429:
        raise HTTPException(502, "Mapbox rate limit reached. Try again shortly.")
    if resp.status_code >= 400:
        raise HTTPException(502, f"Mapbox {what} failed ({resp.status_code}).")


async def _get(url, params, what):
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, params=params)
    except httpx.RequestError as exc:
        raise HTTPException(502, f"Could not reach Mapbox for {what}: {exc.__class__.__name__}")
    _check(resp, what)
    return resp.json()


async def geocode(query):
    """Returns {'lat', 'lng', 'name'}. Accepts an address or 'lat,lng'."""
    direct = parse_lat_lng(query)
    if direct:
        return {"lat": direct[0], "lng": direct[1], "name": query}

    _require_token()
    data = await _get(
        "https://api.mapbox.com/search/geocode/v6/forward",
        {
            "q": query,
            "limit": 1,
            "country": "us",
            "proximity": "-122.4194,37.7749",   # bias toward SF
            "bbox": "-123.2,37.0,-121.5,38.2",  # Bay Area
            "access_token": config.MAPBOX_TOKEN,
        },
        "geocoding",
    )
    features = data.get("features") or []
    if not features:
        raise HTTPException(404, f'Could not find "{query}" in the Bay Area.')
    f = features[0]
    lng, lat = f["geometry"]["coordinates"]
    props = f.get("properties", {})
    return {"lat": lat, "lng": lng, "name": props.get("full_address") or props.get("name") or query}


async def fetch_routes(origin, dest):
    """origin/dest are dicts with lat/lng. Returns Mapbox's list of route dicts."""
    _require_token()
    coords = f"{origin['lng']},{origin['lat']};{dest['lng']},{dest['lat']}"
    data = await _get(
        f"https://api.mapbox.com/directions/v5/mapbox/driving-traffic/{coords}",
        {
            "alternatives": "true",
            "geometries": "geojson",
            "overview": "full",
            "annotations": "congestion",
            "access_token": config.MAPBOX_TOKEN,
        },
        "routing",
    )
    routes = data.get("routes") or []
    if data.get("code") != "Ok" or not routes:
        raise HTTPException(404, "No drivable route found between those points.")
    return routes