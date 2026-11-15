"""Настройки участников и просмотр связанных макетов."""
from django.contrib import admin

from layouts.models import Layout
from participants.models import Client, Designer


class LayoutInline(admin.TabularInline):
    model = Layout
    fields = ("title", "version", "status", "deadline")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Designer)
class DesignerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email")
    search_fields = ("name", "email")
    ordering = ("name", "pk")
    list_per_page = 20
    inlines = (LayoutInline,)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "company")
    search_fields = ("name", "email", "company")
    ordering = ("name", "pk")
    list_per_page = 20
    inlines = (LayoutInline,)


admin.site.site_header = "Сервис согласования макетов"
admin.site.site_title = "Управление макетами"
admin.site.index_title = "Администрирование сервиса"
