from django.urls import path
from . import views

urlpatterns = [
    path('', views.BaseListView.as_view(), name='base-list'),
    path('base/<int:pk>/', views.BaseDetailView.as_view(), name='base-detail'),
    path('base/create/', views.BaseCreateView.as_view(), name='base-create'),
    path('base/<int:base_id>/add-node/', views.ResourceNodeCreateView.as_view(), name='node-create'),
    path('base/<int:base_id>/add-facility/', views.FacilityCreateView.as_view(), name='facility-create'),
    
    # New URLs for Resource Node actions
    path('node/<int:pk>/edit/', views.ResourceNodeUpdateView.as_view(), name='node-edit'),
    path('node/<int:pk>/delete/', views.ResourceNodeDeleteView.as_view(), name='node-delete'),
    
    # New URLs for Facility actions
    path('facility/<int:pk>/edit/', views.FacilityUpdateView.as_view(), name='facility-edit'),
    path('facility/<int:pk>/delete/', views.FacilityDeleteView.as_view(), name='facility-delete'),
    path('facility/<int:pk>/toggle/', views.FacilityToggleView.as_view(), name='facility-toggle'),
]