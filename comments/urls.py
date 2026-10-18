from django.urls import path

from . import views

app_name = "comments"

urlpatterns = [
    path("", views.comments, name="list"),
    path("<int:comment_id>/", views.comment_detail, name="detail"),
]
