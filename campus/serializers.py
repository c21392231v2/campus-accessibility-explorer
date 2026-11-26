import math

from rest_framework import serializers

from .models import Facility


class NearbyFacilityQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    radius = serializers.FloatField(max_value=50000)
    category = serializers.CharField(required=False, allow_blank=True)

    def validate_category(self, value):
        if value and value not in dict(Facility.CATEGORY_CHOICES):
            raise serializers.ValidationError("Choose a valid facility category.")
        return value

    def validate(self, attrs):
        if not all(math.isfinite(attrs[key]) for key in ("lat", "lon", "radius")):
            raise serializers.ValidationError("Coordinates and radius must be finite.")
        if attrs["radius"] <= 0:
            raise serializers.ValidationError("Radius must be greater than zero.")
        return attrs
