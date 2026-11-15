"""Административная панель комментариев."""
from django.contrib import admin

from comments.models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "layout",
        "author",
        "comment_date",
        "layout_version",
        "text")
    search_fields = ("text", "layout__title", "author__name")
    list_filter = ("comment_date", "layout_version", "author")
    ordering = ("-comment_date", "pk")
    list_per_page = 20
    list_select_related = ("layout", "author")
    autocomplete_fields = ("layout", "author")
