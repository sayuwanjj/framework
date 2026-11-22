"""Общие действия над записями сервиса в административной панели."""
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse


class EditActionMixin:
    actions = ("edit_selected",)

    def get_action_choices(self, request, default_choices=None):
        return super().get_action_choices(
            request, default_choices=[("", "Выберите действие")])

    @admin.action(description="Редактировать выбранную запись",
                  permissions=["change"])
    def edit_selected(self, request, queryset):
        selected = list(queryset[:2])
        if len(selected) != 1:
            self.message_user(
                request, "Для редактирования выберите ровно одну запись.",
                level=messages.WARNING)
            return None
        obj = selected[0]
        if not self.has_change_permission(request, obj):
            self.message_user(
                request, "Нет прав на редактирование этой записи.",
                level=messages.ERROR)
            return None
        opts = self.model._meta
        url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_change",
            args=[obj.pk], current_app=self.admin_site.name)
        return HttpResponseRedirect(url)
