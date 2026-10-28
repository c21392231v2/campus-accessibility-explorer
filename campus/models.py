from django.contrib.gis.db import models


class Facility(models.Model):
    CATEGORY_CHOICES = [
        ('entrance', 'Accessible entrance'),
        ('lift', 'Lift'),
        ('toilet', 'Accessible toilet'),
        ('parking', 'Accessible parking'),
        ('other', 'Other'),
    ]
    

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    location = models.PointField(srid=4326)

    def __str__(self):
        return self.name

class CampusArea(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    boundary = models.PolygonField(srid=4326)

    def __str__(self):
        return self.name