"""Настройки участников и просмотр связанных макетов."""
from django.contrib import admin

from layouts.admin_actions import EditActionMixin
from layouts.models import Layout
from participants.models import Client, Designer


class LayoutInline(admin.StackedInline):
    model = Layout
    readonly_fields = ("deadline", "is_revised", "slug")
    extra = 0
    can_delete = True
    show_change_link = True

    def get_fields(self, request, obj=None):
        participant = "client" if self.parent_model is Designer else "designer"
        return (
            "title", participant, "version", "status", "sent_date",
            "approval_days", "image", "deadline", "is_revised", "slug",
        )


@admin.register(Designer)
class DesignerAdmin(EditActionMixin, admin.ModelAdmin):
    list_display = ("id", "name", "email")
    search_fields = ("name", "email")
    ordering = ("name", "pk")
    list_per_page = 20
    inlines = (LayoutInline,)


@admin.register(Client)
class ClientAdmin(EditActionMixin, admin.ModelAdmin):
    list_display = ("id", "name", "email", "company")
    search_fields = ("name", "email", "company")
    ordering = ("name", "pk")
    list_per_page = 20
    inlines = (LayoutInline,)


admin.site.site_header = "Сервис согласования макетов"
admin.site.site_title = "Управление макетами"
admin.site.index_title = "Администрирование сервиса"
