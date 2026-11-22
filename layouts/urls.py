from django.urls import path

from . import views

app_name = "layouts"

urlpatterns = [
    path("create/", views.layout_create, name="create"),
    path("<int:layout_id>/edit/", views.layout_update, name="update"),
    path("<int:layout_id>/cancel/", views.layout_cancel, name="cancel"),
    path("", views.layouts, name="list"),
    path("search/", views.search, name="search"),
    path("overdue/", views.overdue, name="overdue"),
    path("statistics/", views.statistics, name="statistics"),
    path("by-slug/<slug:slug>/", views.layout_detail, name="detail_by_slug"),
    path("<int:layout_id>/", views.layout_detail, name="detail"),
]
