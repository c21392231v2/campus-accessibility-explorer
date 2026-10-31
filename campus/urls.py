from django.urls import path

from . import views

urlpatterns = [
    path('', views.map_page, name='map_page'),
    path('api/facilities/', views.facility_list, name='facility_list'),
    path('api/facilities/nearby/', views.nearby_facilities, name='nearby_facilities'),
    path(
        'api/areas/<int:area_id>/facilities/',
        views.facilities_in_area,
        name='facilities_in_area',
    ),
    path('api/areas/', views.area_list, name='area_list'),
    path(
        'api/areas/<int:area_id>/paths/',
        views.paths_in_area,
        name='paths_in_area',
    ),

    path(
    'api/facilities/create/',
    views.create_facility,
    name='create_facility',
    ),

    path(
        'api/facilities/<int:facility_id>/',
        views.facility_detail,
        name='facility_detail',
    ),
]