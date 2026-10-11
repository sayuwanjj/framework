from django.urls import path

from . import views

urlpatterns = [
    path("", views.layouts, name="layouts"),
    path("<int:layout_id>/", views.layout_detail, name="layout_detail"),
]
