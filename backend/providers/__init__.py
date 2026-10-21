"""
Provider registry. The rest of the app only calls the functions at the bottom of this file.
To add a data source, see the instructions at the top of providers/base.py.
"""
import asyncio
import importlib

from fastapi import HTTPException

import config
from geo import parse_lat_lng
from .base import Place
from .chp import ChpIncidents
from .nominatim import NominatimGeocoder
from .osrm import OsrmRouting


MODES = ("car", "walk", "bike")


def _optional(module, class_name):
    """Loads a provider that needs a key. If its file is missing or broken, skip it with a
    warning instead of crashing the whole app."""
    try:
        return getattr(importlib.import_module(f".{module}", __name__), class_name)
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: skipping provider '{module}' ({exc.__class__.__name__}: {exc}). "
              f"Run check_install.py to find the bad file.")
        return None


def _present(mapping):
    return {name: cls for name, cls in mapping.items() if cls is not None}


# name -> class. Add new providers here.
ROUTING = _present({
    "google": _optional("google_routes", "GoogleRouting"),
    "tomtom": _optional("tomtom", "TomTomRouting"),
    "osrm": OsrmRouting,
})
GEOCODING = {"nominatim": NominatimGeocoder}
INCIDENTS = _present({
    "chp": ChpIncidents,
    "511": _optional("incidents_511", "Incidents511"),
})


def _build(registry, order, kind):
    instances = []
    for name in order:
        cls = registry.get(name)
        if cls is None:
            print(f"WARNING: unknown {kind} provider '{name}' (available: {', '.join(registry)})")
        else:
            instances.append(cls())
    return instances


# Everything listed in .env, whether or not it has a key.
ALL = {
    "routing": _build(ROUTING, config.ROUTING_ORDER, "routing"),
    "geocoding": _build(GEOCODING, config.GEOCODER_ORDER, "geocoding"),
    "incidents": _build(INCIDENTS, config.INCIDENT_SOURCES, "incident"),
}


def active(kind):
    return [p for p in ALL[kind] if p.configured]


async def geocode(query) -> Place:
    """Accepts 'lat,lng' or an address. Tries each configured geocoder in order."""
    direct = parse_lat_lng(query)
    if direct:
        return Place(direct[0], direct[1], query)

    last = None
    for g in active("geocoding"):
        try:
            return await g.geocode(query)
        except HTTPException as e:
            print(f"[geocoding] {g.name}: {e.detail}")
            last = e
    raise last or HTTPException(502, "No geocoding provider is configured.")


async def find_routes(origin: Place, dest: Place, mode="car"):
    """Returns (routes, provider). Tries each configured provider that supports this travel mode."""
    if mode not in MODES:
        raise HTTPException(400, f"Unknown travel mode '{mode}'. Use car, walk, or bike.")
    candidates = [p for p in active("routing") if mode in getattr(p, "modes", ("car",))]
    if not candidates:
        raise HTTPException(502, f"No routing provider is configured for '{mode}'.")

    errors = []
    for p in candidates:
        try:
            # Providers that only do cars keep their original two-argument method.
            routes = await (p.fetch_routes(origin, dest) if mode == "car" else p.fetch_routes(origin, dest, mode))
            if routes:
                return routes, p
        except HTTPException as e:
            if e.status_code in (400, 404):
                raise  # no route, or too far: switching provider will not help
            print(f"[routing] {p.name} failed: {e.detail}")
            errors.append(f"{p.name}: {e.detail}")
    raise HTTPException(502, "All routing providers failed. " + "; ".join(errors))


async def fetch_incidents():
    """Incidents from every configured source, merged, with duplicates removed."""
    lists = await asyncio.gather(*(p.fetch() for p in active("incidents")))
    seen = {}
    for lst in lists:
        for i in lst:
            key = (i.kind, round(i.lat, 3), round(i.lng, 3))  # same kind within about 100 m
            if key not in seen or i.delay_minutes > seen[key].delay_minutes:
                seen[key] = i
    return list(seen.values())


async def raw_incidents(source=None):
    candidates = active("incidents")
    if source:
        candidates = [p for p in candidates if p.name == source.lower()]
    if not candidates:
        raise HTTPException(404, "No such incident source is configured.")
    return {"source": candidates[0].name, "records": await candidates[0].raw()}


async def check_all():
    """One tiny real call per provider, so you can see what works."""
    result = {}
    for kind, providers in ALL.items():
        result[kind] = {}
        for p in providers:
            if not p.configured:
                result[kind][p.name] = {"ok": None, "note": p.not_configured_note()}
                continue
            try:
                result[kind][p.name] = await p.check()
            except HTTPException as e:
                result[kind][p.name] = {"ok": False, "error": e.detail}
            except Exception as e:  # noqa: BLE001
                result[kind][p.name] = {"ok": False, "error": e.__class__.__name__}
    return result