from django.contrib import admin
from .models import Facility, CampusArea, CampusPath
from django.contrib.gis.admin import GISModelAdmin


@admin.register(Facility)
class FacilityAdmin(GISModelAdmin):
    list_display = ('name', 'category', 'location')
    list_filter = ('category',)
    search_fields = ('name', 'description')

@admin.register(CampusArea)
class CampusAreaAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

@admin.register(CampusPath)
class CampusPathAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')