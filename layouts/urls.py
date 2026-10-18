from django.urls import path

from . import views

app_name = "layouts"

urlpatterns = [
    path("", views.layouts, name="list"),
    path("<int:layout_id>/", views.layout_detail, name="detail"),
]
