# src/zones/zone_checker.py

import json
from shapely.geometry import Point, Polygon
from src.paths import get_user_data_path

class ZoneChecker:
    def __init__(self, zones_path=None):
        if zones_path is None:
            zones_path = get_user_data_path("data/zonas/zonas.json")

        with open(zones_path, 'r') as f:
            self.zones = json.load(f)

        self.polygons = {}
        for name, points in self.zones.items():
            self.polygons[name] = Polygon(points)

    def check(self, x, y):
        point = Point(x, y)
        results = {}
        for name, polygon in self.polygons.items():
            results[name] = polygon.contains(point)
        return results
