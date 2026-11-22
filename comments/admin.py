"""Административная панель комментариев."""
from django.contrib import admin

from comments.models import Comment
from layouts.admin_actions import EditActionMixin


@admin.register(Comment)
class CommentAdmin(EditActionMixin, admin.ModelAdmin):
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
