from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.gis.geos import Point, Polygon, LineString

from campus.models import Facility, CampusArea, CampusPath


DISCLAIMER = (
    "Synthetic demonstration data near Grangegorman. "
    "Locations, boundaries, routes and accessibility are not verified."
)


class Command(BaseCommand):
    help = "Create or update the Grangegorman demonstration dataset."

    @transaction.atomic
    def handle(self, *args, **options):
        # Approximate demonstration rectangle, not the official campus boundary.
        boundary = Polygon(
            (
                (-6.2820, 53.3530),
                (-6.2750, 53.3530),
                (-6.2750, 53.3580),
                (-6.2820, 53.3580),
                (-6.2820, 53.3530),
            ),
            srid=4326,
        )

        CampusArea.objects.update_or_create(
            name="Grangegorman Demo Area",
            defaults={
                "description": DISCLAIMER,
                "boundary": boundary,
            },
        )

        facilities = [
            ("Grangegorman Demo Entrance", "entrance", -6.2785, 53.3540),
            ("Grangegorman Demo Lift", "lift", -6.2780, 53.3550),
            ("Grangegorman Demo Toilet", "toilet", -6.2775, 53.3560),
            ("Grangegorman Demo Parking", "parking", -6.2800, 53.3545),
        ]

        for name, category, longitude, latitude in facilities:
            Facility.objects.update_or_create(
                name=name,
                defaults={
                    "category": category,
                    "description": DISCLAIMER,
                    "location": Point(longitude, latitude, srid=4326),
                },
            )

        CampusPath.objects.update_or_create(
            name="Grangegorman Demo Path",
            defaults={
                "description": DISCLAIMER,
                "route": LineString(
                    (-6.2785, 53.3540),
                    (-6.2780, 53.3550),
                    (-6.2775, 53.3560),
                    srid=4326,
                ),
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data ready: 1 area, 4 facilities and 1 path."
            )
        )