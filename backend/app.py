"""
Traffic API (FastAPI).

Run:   python app.py
Docs:  http://localhost:3000/docs
Check: http://localhost:3000/check-sources
"""
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

import config
import providers
from route_service import get_routes, get_trips


@asynccontextmanager
async def lifespan(app):
    for kind in ("routing", "geocoding", "incidents"):
        names = ", ".join(p.name for p in providers.active(kind)) or "none"
        print(f"{kind}: {names}")

    task = None
    if config.LOG_ENABLED:
        from logger_job import run_logger  # imported lazily so the DB is only created when needed

        task = asyncio.create_task(run_logger())
    yield
    if task:
        task.cancel()


app = FastAPI(title="Traffic API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/", include_in_schema=False)
async def home():
    return RedirectResponse("/docs")


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/check-sources")
async def check_sources():
    """One tiny real call to every provider listed in .env, with a readable result for each."""
    return await providers.check_all()


# GET /trips?from=Mission Dolores Park, San Francisco&to=Ferry Building, San Francisco
@app.get("/trips")
async def trips(
    from_: str = Query(..., alias="from", min_length=1, description='Address or "lat,lng"'),
    to: str = Query(..., min_length=1, description='Address or "lat,lng"'),
):
    """Routes for car, walking, and cycling in one response."""
    return await get_trips(from_, to)


# GET /routes?from=37.7749,-122.4194&to=Ferry Building, San Francisco&mode=walk
@app.get("/routes")
async def routes(
    from_: str = Query(..., alias="from", min_length=1, description='Address or "lat,lng"'),
    to: str = Query(..., min_length=1, description='Address or "lat,lng"'),
    mode: str = Query("car", description="car, walk, or bike"),
):
    return await get_routes(from_, to, mode)


@app.get("/incidents")
async def incidents():
    return {"incidents": [i.to_dict() for i in await providers.fetch_incidents()]}


@app.get("/incidents/raw")
async def incidents_raw(source: Optional[str] = Query(None, description="chp or 511. Defaults to the first configured.")):
    """First few unprocessed records from a source, to check field names against what the parser expects."""
    data = await providers.raw_incidents(source)
    return {"source": data["source"], "count": len(data["records"]), "sample": data["records"][:3]}


if __name__ == "__main__":
    import os

    here = os.path.dirname(os.path.abspath(__file__))
    # Watch only the backend folder, not the whole project (node_modules etc.).
    uvicorn.run("app:app", host="0.0.0.0", port=3000, reload=True, reload_dirs=[here])