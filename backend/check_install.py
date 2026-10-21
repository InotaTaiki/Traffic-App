"""
Checks that every backend file is present and is the current version, without importing the app.

Run from the backend folder:   python check_install.py
"""
import ast
import os

BASE = os.path.dirname(os.path.abspath(__file__))

# file -> names it must define at the top level
EXPECTED = {
    "app.py": ["app"],
    "config.py": ["ROUTING_ORDER", "INCIDENT_SOURCES", "GEOCODER_ORDER"],
    "db.py": ["insert_log"],
    "geo.py": ["parse_lat_lng", "distance_to_polyline_m"],
    "logger_job.py": ["run_logger"],
    "route_service.py": ["get_routes"],
    "providers/__init__.py": ["geocode", "find_routes", "fetch_incidents", "raw_incidents", "check_all"],
    "providers/base.py": ["Place", "Route", "Incident", "Provider", "RoutingProvider", "Geocoder", "IncidentProvider"],
    "providers/chp.py": ["ChpIncidents"],
    "providers/google_routes.py": ["GoogleRouting"],
    "providers/incidents_511.py": ["Incidents511"],
    "providers/nominatim.py": ["NominatimGeocoder"],
    "providers/osrm.py": ["OsrmRouting"],
    "providers/tomtom.py": ["TomTomRouting"],
}

# Old files from earlier versions. They should be deleted from the backend folder.
LEFTOVERS = ["osrm.py", "tomtom.py", "chp.py", "geocoder.py", "mapbox.py", "incidents511.py"]


def top_level_names(tree):
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
    return names


bad = []
for rel, needed in EXPECTED.items():
    path = os.path.join(BASE, *rel.split("/"))
    if not os.path.exists(path):
        bad.append(f"MISSING  {rel}")
        continue
    if os.path.getsize(path) == 0:
        bad.append(f"EMPTY    {rel} (0 bytes)")
        continue
    try:
        with open(path, encoding="utf-8-sig") as f:
            names = top_level_names(ast.parse(f.read()))
    except SyntaxError as e:
        bad.append(f"BROKEN   {rel} (syntax error on line {e.lineno}, probably a partial copy)")
        continue
    missing = [n for n in needed if n not in names]
    if missing:
        bad.append(f"OLD/WRONG {rel} (does not define: {', '.join(missing)})")
    else:
        print(f"ok       {rel}")

for name in LEFTOVERS:
    if os.path.exists(os.path.join(BASE, name)):
        bad.append(f"DELETE   {name} (old file in the backend folder)")

print()
if bad:
    print("Problems found:")
    for line in bad:
        print("  " + line)
    print("\nFix: replace the files marked MISSING, EMPTY, BROKEN, or OLD/WRONG with the ones from backend-python.zip,")
    print("and delete the files marked DELETE. Then run this check again.")
else:
    print("All files look right. You can run app.py.")