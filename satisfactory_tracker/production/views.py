from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from .models import *
from .forms import BaseForm, ResourceNodeForm, FacilityForm
from decimal import Decimal, ROUND_HALF_UP
from django.views import View
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist

class BaseListView(ListView):
    model = Base
    template_name = 'production/base_list.html'
    context_object_name = 'bases'

class BaseDetailView(DetailView):
    model = Base
    template_name = 'production/base_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base = self.get_object()
        
        # Debug information
        print(f"Base ID: {base.id}")
        print(f"Nodes: {base.nodes.all()}")
        print(f"Facilities: {base.facilities.all()}")
        
        # Calculate production rates
        production = {}
        consumption = {}
        net_production = {}
        
        # Add node production
        for node in base.nodes.all():
            resource_type = node.resource_type.name
            print(f"Processing node {node.id}: {resource_type}")
            production[resource_type] = production.get(resource_type, 0) + node.output_rate
            
        # Add facility production/consumption
        for facility in base.facilities.filter(is_active=True):
            try:
                recipe_items = facility.recipe.items.all()
                clock_factor = facility.clock_speed / 100.0
                print(f"Processing facility {facility.id}: {facility.recipe.name}")
                
                for item in recipe_items:
                    resource_name = item.resource_type.name
                    adjusted_rate = item.rate * clock_factor
                    
                    if item.item_type == 'input':
                        consumption[resource_name] = consumption.get(resource_name, 0) + adjusted_rate
                    else:  # output
                        production[resource_name] = production.get(resource_name, 0) + adjusted_rate
            except ObjectDoesNotExist as e:
                print(f"Error processing facility {facility.id}: {e}")
        
        # Calculate net production
        all_resources = set(list(production.keys()) + list(consumption.keys()))
        for resource in all_resources:
            prod = production.get(resource, 0)
            cons = consumption.get(resource, 0)
            net_production[resource] = prod - cons
        
        print("Final production:", production)
        print("Final consumption:", consumption)
        print("Final net production:", net_production)
        
        context['production'] = production
        context['consumption'] = consumption
        context['net_production'] = net_production
        return context

class BaseCreateView(CreateView):
    model = Base
    form_class = BaseForm
    template_name = 'production/base_form.html'
    success_url = reverse_lazy('base-list')

class ResourceNodeCreateView(CreateView):
    model = ResourceNode
    form_class = ResourceNodeForm
    template_name = 'production/resourcenode_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_id'] = self.kwargs.get('base_id')  # Get base_id from URL kwargs
        return context
    
    def form_valid(self, form):
        base_id = self.kwargs.get('base_id')
        form.instance.base_id = base_id
        response = super().form_valid(form)
        return response

    def get_success_url(self):
        return reverse_lazy('base-detail', kwargs={'pk': self.kwargs.get('base_id')})

class FacilityCreateView(CreateView):
    model = Facility
    form_class = FacilityForm
    template_name = 'production/facility_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_id'] = self.kwargs.get('base_id')  # Get base_id from URL kwargs
        return context
    
    def form_valid(self, form):
        base_id = self.kwargs.get('base_id')
        form.instance.base_id = base_id
        response = super().form_valid(form)
        return response

    def get_success_url(self):
        return reverse_lazy('base-detail', kwargs={'pk': self.kwargs.get('base_id')})

class ResourceNodeUpdateView(UpdateView):
    model = ResourceNode
    form_class = ResourceNodeForm
    template_name = 'production/resourcenode_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_id'] = self.object.base.id
        return context

    def get_success_url(self):
        return reverse_lazy('base-detail', kwargs={'pk': self.object.base.id})

class ResourceNodeDeleteView(DeleteView):
    model = ResourceNode
    template_name = 'production/confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('base-detail', kwargs={'pk': self.object.base.id})

class FacilityUpdateView(UpdateView):
    model = Facility
    form_class = FacilityForm
    template_name = 'production/facility_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_id'] = self.object.base.id
        return context

    def get_success_url(self):
        return reverse_lazy('base-detail', kwargs={'pk': self.object.base.id})

class FacilityDeleteView(DeleteView):
    model = Facility
    template_name = 'production/confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('base-detail', kwargs={'pk': self.object.base.id})

class FacilityToggleView(View):
    def get(self, request, pk):
        facility = get_object_or_404(Facility, pk=pk)
        facility.is_active = not facility.is_active
        facility.save()
        return redirect('base-detail', pk=facility.base.id)