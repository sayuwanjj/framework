"""Административная панель макетов и встроенных комментариев."""
from django.contrib import admin

from comments.models import Comment
from layouts.models import Layout


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    show_change_link = True
    autocomplete_fields = ("author",)


@admin.register(Layout)
class LayoutAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "version",
        "designer",
        "client",
        "status",
        "sent_date",
        "deadline")
    list_display_links = ("id", "title")
    search_fields = (
        "title",
        "designer__name",
        "client__name",
        "client__company")
    list_filter = ("status", "designer", "client", "sent_date")
    ordering = ("deadline", "pk")
    list_per_page = 20
    list_select_related = ("designer", "client")
    autocomplete_fields = ("designer", "client")
    readonly_fields = ("deadline", "slug", "is_revised")
    date_hierarchy = "sent_date"
    inlines = (CommentInline,)
