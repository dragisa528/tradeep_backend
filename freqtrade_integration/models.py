from django.db import models

# Create your models here.


class MarketData(models.Model):
    timestamp = models.DateTimeField()
    price = models.FloatField()
    volume = models.FloatField()
    # add other fields as needed

