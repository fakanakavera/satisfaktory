from django.db import models

class Base(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ResourceType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class MinerType(models.Model):
    name = models.CharField(max_length=100)
    base_rate = models.FloatField()

    def __str__(self):
        return self.name

class BuildingType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class ResourceNode(models.Model):
    PURITY_CHOICES = [
        ('Impure', 'Impure'),
        ('Normal', 'Normal'),
        ('Pure', 'Pure'),
    ]
    
    base = models.ForeignKey(Base, on_delete=models.CASCADE, null=True, related_name='nodes')
    resource_type = models.ForeignKey(ResourceType, on_delete=models.CASCADE)
    purity = models.CharField(max_length=10, choices=PURITY_CHOICES)
    miner_type = models.ForeignKey(MinerType, on_delete=models.CASCADE)
    clock_speed = models.FloatField(default=100.0)

    def __str__(self):
        return f"{self.resource_type.name} - {self.purity} - {self.miner_type.name} - {self.clock_speed}%"
    
    @property
    def output_rate(self):
        purity_multiplier = {"Impure": 0.5, "Normal": 1, "Pure": 2}
        return purity_multiplier[self.purity] * self.miner_type.base_rate * (self.clock_speed / 100.0)

class Recipe(models.Model):
    name = models.CharField(max_length=100, unique=True)
    building_type = models.ForeignKey(BuildingType, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class RecipeItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ('input', 'Input'),
        ('output', 'Output'),
    ]
    
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='items')
    resource_type = models.ForeignKey(ResourceType, on_delete=models.CASCADE)
    rate = models.FloatField()
    item_type = models.CharField(max_length=6, choices=ITEM_TYPE_CHOICES)
    
    def __str__(self):
        return f"{self.recipe.name} - {self.resource_type.name} ({self.item_type})"

class Facility(models.Model):
    base = models.ForeignKey(Base, on_delete=models.CASCADE, related_name='facilities')
    facility_type = models.ForeignKey(BuildingType, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    clock_speed = models.FloatField(default=100.0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.facility_type.name} - {self.recipe.name}"