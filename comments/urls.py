from django.urls import path

from . import views

urlpatterns = [
    path("", views.comments, name="comments"),
    path("<int:comment_id>/", views.comment_detail, name="comment_detail"),
]
