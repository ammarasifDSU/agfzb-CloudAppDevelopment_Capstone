from django.contrib import admin
from .models import CarMake, CarModel


# Register your models here.
admin.site.register(CarMake)

admin.site.register(CarModel)



# CarModelInline class

class CarModelInline:
    pass


# Register models here
