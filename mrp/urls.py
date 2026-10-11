from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("materials/", views.materials, name="materials"),
    path("bom/", views.bom, name="bom"),
    path("inventory/", views.inventory, name="inventory"),
    path("mps/", views.mps, name="mps"),
    path("mrp/run/", views.mrp_run, name="mrp_run"),
    path("mrp/results/", views.mrp_results, name="mrp_results"),
    path("formula/", views.formula, name="formula"),
]
