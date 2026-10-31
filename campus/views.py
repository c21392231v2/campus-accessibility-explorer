import json
import math

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.views.decorators.http import require_http_methods

from .models import Facility, CampusArea, CampusPath


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

def paths_in_area(request, area_id):
    try:
        area = CampusArea.objects.get(pk=area_id)
    except CampusArea.DoesNotExist:
        return JsonResponse(
            {'error': 'Campus area not found.'},
            status=404,
        )

    paths = CampusPath.objects.filter(
        route__intersects=area.boundary
    )

    features = []

    for path in paths:
        features.append({
            'type': 'Feature',
            'geometry': json.loads(path.route.geojson),
            'properties': {
                'id': path.id,
                'name': path.name,
                'description': path.description,
            },
        })

    return JsonResponse({
        'type': 'FeatureCollection',
        'area': area.name,
        'features': features,
    })

def validate_facility_data(data):
    """Validate JSON input and return cleaned facility values."""
    if not isinstance(data, dict):
        raise ValueError('The request must contain a JSON object.')

    name = data.get('name')
    category = data.get('category')
    description = data.get('description', '')
    longitude = data.get('longitude')
    latitude = data.get('latitude')

    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
        raise ValueError('Name is required and must be 100 characters or less.')

    valid_categories = {value for value, _ in Facility.CATEGORY_CHOICES}

    if category not in valid_categories:
        raise ValueError('Choose a valid facility category.')

    if not isinstance(description, str):
        raise ValueError('Description must be text.')

    if isinstance(longitude, bool) or isinstance(latitude, bool):
        raise ValueError('Coordinates must be numbers.')

    try:
        longitude = float(longitude)
        latitude = float(latitude)
    except (TypeError, ValueError):
        raise ValueError('Longitude and latitude must be numbers.')

    if not math.isfinite(longitude) or not math.isfinite(latitude):
        raise ValueError('Coordinates must be finite numbers.')

    if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
        raise ValueError('Coordinates are outside the valid range.')

    return {
        'name': name.strip(),
        'category': category,
        'description': description,
        'location': Point(longitude, latitude, srid=4326),
    }


def read_json_body(request):
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError('Request body must contain valid JSON.')


def facility_response(facility):
    return {
        'id': facility.id,
        'name': facility.name,
        'category': facility.category,
        'description': facility.description,
        'longitude': facility.location.x,
        'latitude': facility.location.y,
    }


@require_http_methods(['POST'])
def create_facility(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'error': 'Staff login required.'}, status=403)

    try:
        data = read_json_body(request)
        values = validate_facility_data(data)
    except ValueError as error:
        return JsonResponse({'error': str(error)}, status=400)

    facility = Facility.objects.create(**values)

    return JsonResponse(facility_response(facility), status=201)


@require_http_methods(['GET', 'PUT', 'DELETE'])
def facility_detail(request, facility_id):
    try:
        facility = Facility.objects.get(pk=facility_id)
    except Facility.DoesNotExist:
        return JsonResponse({'error': 'Facility not found.'}, status=404)

    if request.method == 'GET':
        return JsonResponse(facility_response(facility))

    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'error': 'Staff login required.'}, status=403)

    if request.method == 'DELETE':
        facility.delete()
        return JsonResponse({'message': 'Facility deleted.'})

    try:
        data = read_json_body(request)
        values = validate_facility_data(data)
    except ValueError as error:
        return JsonResponse({'error': str(error)}, status=400)

    for field, value in values.items():
        setattr(facility, field, value)

    facility.save()

    return JsonResponse(facility_response(facility))