from django.contrib import admin
from django.urls import path

from web import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("empresa/<str:symbol>/", views.empresa, name="empresa"),
    path("admin/", admin.site.urls),
]
