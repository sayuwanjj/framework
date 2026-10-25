from django.urls import path

from . import views

app_name = "layouts"

urlpatterns = [
    path("", views.layouts, name="list"),
    path("search/", views.search, name="search"),
    path("overdue/", views.overdue, name="overdue"),
    path("statistics/", views.statistics, name="statistics"),
    path("<int:layout_id>/", views.layout_detail, name="detail"),
]
