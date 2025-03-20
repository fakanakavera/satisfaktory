from django.contrib import admin
from .models import *

admin.site.register(Base)
admin.site.register(ResourceType)
admin.site.register(MinerType)
admin.site.register(BuildingType)
admin.site.register(ResourceNode)
admin.site.register(Recipe)
admin.site.register(RecipeItem)
admin.site.register(Facility)