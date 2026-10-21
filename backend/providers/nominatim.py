"""OpenStreetMap Nominatim geocoder. No key, no account. Policy: max 1 request/second, cache results."""
import asyncio
import time

import httpx
from fastapi import HTTPException

import config
from .base import Geocoder, Place

URL = "https://nominatim.openstreetmap.org/search"
MIN_GAP_SECONDS = 1.1


class NominatimGeocoder(Geocoder):
    name = "nominatim"

    def __init__(self):
        self._cache = {}
        self._lock = asyncio.Lock()
        self._last_call = 0.0

    async def geocode(self, query):
        key = query.strip().lower()
        if key in self._cache:
            return self._cache[key]

        async with self._lock:
            if key in self._cache:
                return self._cache[key]
            wait = MIN_GAP_SECONDS - (time.monotonic() - self._last_call)
            if wait > 0:
                await asyncio.sleep(wait)
            try:
                async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": config.USER_AGENT}) as client:
                    resp = await client.get(URL, params={
                        "q": query, "format": "jsonv2", "limit": 1,
                        "viewbox": "-123.2,38.2,-121.5,37.0", "bounded": 0,
                    })
            except httpx.RequestError as exc:
                raise HTTPException(502, f"Could not reach Nominatim: {exc.__class__.__name__}")
            finally:
                self._last_call = time.monotonic()

        if resp.status_code in (403, 429):
            raise HTTPException(502, f"Nominatim refused the request ({resp.status_code}). Wait a minute and retry.")
        if resp.status_code >= 400:
            raise HTTPException(502, f"Nominatim failed ({resp.status_code}).")

        results = resp.json()
        if not results:
            raise HTTPException(404, "Could not find the address. Try adding the city and state or the ZIP code.")
        item = results[0]
        place = Place(float(item["lat"]), float(item["lon"]), item.get("display_name") or query)
        self._cache[key] = place
        return place