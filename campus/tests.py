from django.contrib.gis.geos import LineString, Point, Polygon
from django.test import TestCase
from django.urls import reverse

from .models import CampusArea, CampusPath, Facility


class SpatialQueryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # A small synthetic area around a point in Dublin.
        cls.area = CampusArea.objects.create(
            name="Test campus",
            boundary=Polygon(
                (
                    (-6.280, 53.350),
                    (-6.270, 53.350),
                    (-6.270, 53.360),
                    (-6.280, 53.360),
                    (-6.280, 53.350),
                ),
                srid=4326,
            ),
        )

        cls.inside = Facility.objects.create(
            name="Inside facility",
            category="lift",
            location=Point(-6.275, 53.355, srid=4326),
        )
        cls.outside = Facility.objects.create(
            name="Outside facility",
            category="toilet",
            location=Point(-6.300, 53.355, srid=4326),
        )

        cls.crossing_path = CampusPath.objects.create(
            name="Crossing path",
            route=LineString(
                (-6.285, 53.355),
                (-6.265, 53.355),
                srid=4326,
            ),
        )
        cls.distant_path = CampusPath.objects.create(
            name="Distant path",
            route=LineString(
                (-6.310, 53.355),
                (-6.300, 53.355),
                srid=4326,
            ),
        )

    def test_nearby_search_returns_only_facilities_in_radius(self):
        response = self.client.get(
            reverse("nearby_facilities"),
            {"lat": 53.355, "lon": -6.275, "radius": 500},
        )

        self.assertEqual(response.status_code, 200)
        ids = {feature["properties"]["id"] for feature in response.json()["features"]}
        self.assertIn(self.inside.id, ids)
        self.assertNotIn(self.outside.id, ids)

    def test_area_search_returns_only_facilities_in_area(self):
        response = self.client.get(
            reverse("facilities_in_area", args=[self.area.id])
        )

        self.assertEqual(response.status_code, 200)
        ids = {feature["properties"]["id"] for feature in response.json()["features"]}
        self.assertIn(self.inside.id, ids)
        self.assertNotIn(self.outside.id, ids)

    def test_path_search_returns_only_intersecting_paths(self):
        response = self.client.get(
            reverse("paths_in_area", args=[self.area.id])
        )

        self.assertEqual(response.status_code, 200)
        ids = {feature["properties"]["id"] for feature in response.json()["features"]}
        self.assertIn(self.crossing_path.id, ids)
        self.assertNotIn(self.distant_path.id, ids)

    def test_nearby_search_rejects_invalid_radius(self):
        response = self.client.get(
            reverse("nearby_facilities"),
            {"lat": 53.355, "lon": -6.275, "radius": -1},
        )

        self.assertEqual(response.status_code, 400)

    def test_nearby_search_filters_by_category(self):
        Facility.objects.create(
            name="Nearby toilet",
            category="toilet",
            location=Point(-6.2755, 53.355, srid=4326),
        )

        response = self.client.get(
            reverse("nearby_facilities"),
            {
                "lat": 53.355,
                "lon": -6.275,
                "radius": 500,
                "category": "toilet",
            },
        )

        self.assertEqual(response.status_code, 200)
        names = {
            feature["properties"]["name"]
            for feature in response.json()["features"]
        }
        self.assertEqual(names, {"Nearby toilet"})

    def test_nearby_search_rejects_invalid_category(self):
        response = self.client.get(
            reverse("nearby_facilities"),
            {
                "lat": 53.355,
                "lon": -6.275,
                "radius": 500,
                "category": "invalid",
            },
        )

        self.assertEqual(response.status_code, 400)