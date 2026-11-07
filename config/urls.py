from django.contrib import admin
from django.urls import path

from web import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("empresa/<str:symbol>/", views.empresa, name="empresa"),
    path("empresa/<str:symbol>/csv/", views.empresa_csv, name="empresa_csv"),
    path("comparar/", views.comparar, name="comparar"),
    path("admin/", admin.site.urls),
]
