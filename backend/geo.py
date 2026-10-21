import math
import re

EARTH_RADIUS_M = 6371000.0
_LATLNG = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")


def parse_lat_lng(text):
    """'37.77,-122.41' -> (37.77, -122.41), otherwise None."""
    m = _LATLNG.match(text)
    if not m:
        return None
    lat, lng = float(m.group(1)), float(m.group(2))
    if abs(lat) <= 90 and abs(lng) <= 180:
        return lat, lng
    return None


def distance_to_polyline_m(lat, lng, line):
    """Shortest distance in meters from a point to a [[lng, lat], ...] polyline."""
    cos_lat = math.cos(math.radians(lat))

    def x(lo):
        return math.radians(lo - lng) * EARTH_RADIUS_M * cos_lat

    def y(la):
        return math.radians(la - lat) * EARTH_RADIUS_M

    best = math.inf
    for i in range(len(line) - 1):
        ax, ay = x(line[i][0]), y(line[i][1])
        bx, by = x(line[i + 1][0]), y(line[i + 1][1])
        dx, dy = bx - ax, by - ay
        len2 = dx * dx + dy * dy
        # The point is the origin (0, 0) in this local frame.
        t = 0.0 if len2 == 0 else max(0.0, min(1.0, (-ax * dx - ay * dy) / len2))
        best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best