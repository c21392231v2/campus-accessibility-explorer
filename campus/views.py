from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
import json

from .models import Facility, CampusArea


def map_page(request):
    return render(request, 'campus/map.html')


def facility_list(request):
    facilities = Facility.objects.all()

    features = []

    for facility in facilities:
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                # GeoJSON uses longitude first, then latitude.
                'coordinates': [facility.location.x, facility.location.y],
            },
            'properties': {
                'id': facility.id,
                'name': facility.name,
                'category': facility.get_category_display(),
                'description': facility.description,
            },
        })

    return JsonResponse({
        'type': 'FeatureCollection',
        'features': features,
    })

def nearby_facilities(request):
    try:
        latitude = float(request.GET.get('lat', ''))
        longitude = float(request.GET.get('lon', ''))
        radius = float(request.GET.get('radius', ''))

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError('Invalid coordinates.')

        if not (0 < radius <= 50000):
            raise ValueError('Radius must be between 0 and 50,000 metres.')

    except (ValueError, TypeError):
        return JsonResponse(
            {'error': 'Provide valid lat, lon and radius values.'},
            status=400,
        )

    # Point takes longitude first, then latitude.
    centre = Point(longitude, latitude, srid=4326)

    facilities = (
        Facility.objects
        .filter(location__distance_lte=(centre, D(m=radius)))
        .annotate(distance=Distance('location', centre))
        .order_by('distance')
    )

    features = []

    for facility in facilities:
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [facility.location.x, facility.location.y],
            },
            'properties': {
                'id': facility.id,
                'name': facility.name,
                'category': facility.get_category_display(),
                'description': facility.description,
                'distance_metres': round(facility.distance.m),
            },
        })

    return JsonResponse({
        'type': 'FeatureCollection',
        'features': features,
    })

def facilities_in_area(request, area_id):
    try:
        area = CampusArea.objects.get(pk=area_id)
    except CampusArea.DoesNotExist:
        return JsonResponse(
            {'error': 'Campus area not found.'},
            status=404,
        )

    # Find facility points inside or on the boundary of the polygon.
    facilities = Facility.objects.filter(
        location__coveredby=area.boundary
    )

    features = []

    for facility in facilities:
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [
                    facility.location.x,
                    facility.location.y,
                ],
            },
            'properties': {
                'id': facility.id,
                'name': facility.name,
                'category': facility.get_category_display(),
                'description': facility.description,
            },
        })

    return JsonResponse({
        'type': 'FeatureCollection',
        'area': area.name,
        'features': features,
    })

def area_list(request):
    features = []

    for area in CampusArea.objects.all():
        features.append({
            'type': 'Feature',
            'geometry': json.loads(area.boundary.geojson),
            'properties': {
                'id': area.id,
                'name': area.name,
                'description': area.description,
            },
        })

    return JsonResponse({
        'type': 'FeatureCollection',
        'features': features,
    })