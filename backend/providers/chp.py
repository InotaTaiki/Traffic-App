"""California Highway Patrol public incident feed. No key, no account.
Field names come from memory: use /incidents/raw?source=chp to confirm against the real feed."""
import re
import xml.etree.ElementTree as ET

import httpx
from fastapi import HTTPException

import config
from .base import Incident, IncidentProvider

URL = "https://media.chp.ca.gov/sa_xml/sa.xml"


def parse_latlon(text):
    """CHP writes 'lat:lon' in millionths of a degree, with the longitude's minus sign dropped."""
    parts = re.split(r"[:,\s]+", (text or "").strip())
    if len(parts) < 2:
        return None
    try:
        lat, lng = float(parts[0]), float(parts[1])
    except ValueError:
        return None
    if abs(lat) > 1000:
        lat /= 1e6
    if abs(lng) > 1000:
        lng /= 1e6
    if lng > 0:
        lng = -lng  # California
    return (lat, lng) if 32 < lat < 43 and -125 < lng < -113 else None


def classify(log_type):
    """(kind, estimated delay in minutes), or None to ignore the log."""
    t = log_type.lower()
    if "fatal" in t or "1144" in t:
        return "accident", 12
    if "accident" in t or "collision" in t:
        if "non injury" in t or "no inj" in t:
            return "accident", 4
        return ("accident", 8) if "inj" in t else ("accident", 6)
    if any(w in t for w in ("closure", "closed", "sigalert", "sig alert")):
        return "closure", 8
    if "construction" in t or "czp" in t:
        return "construction", 3
    if any(w in t for w in ("hazard", "debris", "animal", "disabled", "stalled", "1125", "traffic control", "1184")):
        return "hazard", 2
    return None


def parse_logs(logs, source="chp"):
    incidents = []
    for log in logs:
        log_type = log.get("LogType", "")
        cls, pos = classify(log_type), parse_latlon(log.get("LATLON", ""))
        if not cls or not pos:
            continue
        kind, delay = cls
        desc = re.sub(r"^[0-9A-Za-z]+\s*-\s*", "", log_type) or kind
        where = log.get("Location", "")
        incidents.append(Incident(
            id=log.get("id") or f"{kind}-{pos[0]}-{pos[1]}", kind=kind,
            label=f"{desc} - {where}" if where else desc,
            delay_minutes=delay, lat=pos[0], lng=pos[1], source=source,
        ))
    return incidents


class ChpIncidents(IncidentProvider):
    name = "chp"

    async def raw(self):
        try:
            async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": config.USER_AGENT}, follow_redirects=True) as client:
                resp = await client.get(URL)
        except httpx.RequestError as exc:
            raise HTTPException(502, f"Could not reach the CHP feed: {exc.__class__.__name__}")
        if resp.status_code >= 400:
            raise HTTPException(502, f"CHP feed request failed ({resp.status_code}).")
        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError:
            raise HTTPException(502, "CHP feed was not valid XML.")

        logs = []
        for log in root.iter("Log"):
            row = {"id": log.get("ID") or ""}
            for child in log:
                row[child.tag] = (child.text or "").strip().strip('"')
            logs.append(row)
        return logs

    async def _fetch(self):
        return parse_logs(await self.raw(), self.name)