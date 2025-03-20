from django import forms
from .models import Base, ResourceNode, Facility

class BaseForm(forms.ModelForm):
    class Meta:
        model = Base
        fields = ['name']

class ResourceNodeForm(forms.ModelForm):
    class Meta:
        model = ResourceNode
        fields = ['resource_type', 'purity', 'miner_type', 'clock_speed']

class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = ['facility_type', 'recipe', 'clock_speed']