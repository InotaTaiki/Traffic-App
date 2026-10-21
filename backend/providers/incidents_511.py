"""511.org Bay Area traffic events. Enabled when API_511_KEY is set.
Field names come from memory: use /incidents/raw?source=511 to confirm against the real feed."""
import json
import re

import httpx
from fastapi import HTTPException

import config
from .base import Incident, IncidentProvider

URL = "https://api.511.org/traffic/events"
BASE_DELAY = {"accident": 6, "closure": 8, "construction": 3, "event": 4}


def _kind(e):
    etype = (e.get("event_type") or "").upper()
    text = f"{e.get('headline') or ''} {' '.join(e.get('event_subtypes') or [])}".lower()
    closed = bool(re.search(r"closed|closure", text))
    if etype == "CONSTRUCTION":
        return "closure" if closed else "construction"
    if etype == "SPECIAL_EVENT":
        return "event"
    if etype == "INCIDENT":
        return "closure" if closed else "accident"
    return None


def _delay(kind, severity):
    s = (severity or "").lower()
    mult = 1.5 if ("severe" in s or "major" in s) else 0.6 if "minor" in s else 1.0
    return max(1, round(BASE_DELAY[kind] * mult))


class Incidents511(IncidentProvider):
    name = "511"
    key_env = "API_511_KEY"
    ttl_seconds = 180  # 511 allows roughly 60 requests/hour

    @property
    def configured(self):
        return bool(config.API_511_KEY)

    async def raw(self):
        try:
            async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": config.USER_AGENT}) as client:
                resp = await client.get(URL, params={"api_key": config.API_511_KEY, "format": "json"})
        except httpx.RequestError as exc:
            raise HTTPException(502, f"Could not reach 511: {exc.__class__.__name__}")
        if resp.status_code in (401, 403):
            raise HTTPException(502, f"511 rejected the API key ({resp.status_code}). Check API_511_KEY.")
        if resp.status_code == 429:
            raise HTTPException(502, "511 rate limit reached (about 60 requests/hour).")
        if resp.status_code >= 400:
            raise HTTPException(502, f"511 request failed ({resp.status_code}).")
        # 511 JSON starts with a byte-order mark, which breaks plain json parsing.
        return json.loads(resp.content.decode("utf-8-sig")).get("events") or []

    async def _fetch(self):
        incidents = []
        for e in await self.raw():
            status = e.get("status")
            if status and status.upper() != "ACTIVE":
                continue
            kind = _kind(e)
            c = (e.get("geography") or {}).get("coordinates")
            if not kind or not isinstance(c, list) or len(c) < 2 or not all(isinstance(x, (int, float)) for x in c[:2]):
                continue
            incidents.append(Incident(
                id=e.get("id") or f"{kind}-{c[0]}-{c[1]}", kind=kind, label=e.get("headline") or kind,
                delay_minutes=_delay(kind, e.get("severity")), lat=c[1], lng=c[0], source=self.name,
            ))
        return incidents