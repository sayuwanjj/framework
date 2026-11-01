"""Тесты моделей и страниц на Django ORM (ПР9).

Запуск: python manage.py test
Django создаёт отдельную тестовую базу, рабочая db.sqlite3 не меняется.
"""

from datetime import date

from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from comments.models import Comment
from layouts.models import Layout
from participants.models import Client, Designer


class LayoutOrmTests(TestCase):
    """Модели, связи и представления приложения layouts."""

    @classmethod
    def setUpTestData(cls):
        cls.designer = Designer.objects.create(
            name="Грязнова Арина", email="gryaznova@example.com"
        )
        cls.idle_designer = Designer.objects.create(
            name="Петров Олег", email="petrov@example.com"
        )
        cls.customer = Client.objects.create(
            name="Иванов Пётр",
            email="ivanov@example.com",
            company="ООО «Ромашка»",
        )
        cls.main_page = Layout.objects.create(
            title="Главная страница",
            designer=cls.designer,
            client=cls.customer,
            sent_date=date(2026, 9, 10),
            approval_days=5,
            status=Layout.STATUS_REVISION,
            version=2,
        )
        cls.card = Layout.objects.create(
            title="Карточка товара",
            designer=cls.designer,
            client=cls.customer,
            sent_date=date(2026, 9, 18),
            approval_days=7,
        )
        cls.banner = Layout.objects.create(
            title="Баннер",
            designer=cls.designer,
            client=cls.customer,
            sent_date=date(2026, 9, 5),
            approval_days=3,
            status=Layout.STATUS_APPROVED,
        )
        for text in ("Увеличить логотип", "Крупнее шрифт"):
            Comment.objects.create(
                layout=cls.main_page,
                author=cls.customer,
                text=text,
                comment_date=date(2026, 9, 13),
                layout_version=1,
            )

    def test_deadline_is_calculated_on_save(self):
        self.assertEqual(self.main_page.deadline, date(2026, 9, 15))

    def test_reverse_relations(self):
        self.assertEqual(self.designer.layouts.count(), 3)
        self.assertEqual(self.main_page.comments.count(), 2)
        self.assertEqual(self.customer.comments.count(), 2)

    def test_protect_does_not_delete_designer_with_layouts(self):
        with self.assertRaises(ProtectedError):
            self.designer.delete()

    def test_cascade_deletes_comments_with_layout(self):
        self.main_page.delete()
        self.assertEqual(Comment.objects.count(), 0)

    def test_send_to_revision_increases_version(self):
        self.card.send_to_revision()
        self.card.refresh_from_db()
        self.assertEqual(self.card.version, 2)
        self.assertEqual(self.card.status, Layout.STATUS_REVISION)

    def test_list_page_is_paginated(self):
        response = self.client.get(reverse("layouts:list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total"], 3)
        self.assertEqual(len(response.context["page_obj"]), 2)
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 2)

    def test_list_filter_by_status(self):
        response = self.client.get(
            reverse("layouts:list"), {"status": Layout.STATUS_APPROVED}
        )
        titles = [item["title"] for item in response.context["layouts"]]
        self.assertEqual(titles, ["Баннер"])

    def test_unknown_sort_and_page_do_not_break_list(self):
        response = self.client.get(
            reverse("layouts:list"), {"sort": "password", "page": "abc"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sort"], "deadline")
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_detail_page_and_404(self):
        url = reverse("layouts:detail", args=[self.main_page.pk])
        response = self.client.get(url)
        self.assertContains(response, "Иванов Пётр")
        missing = self.client.get(reverse("layouts:detail", args=[999]))
        self.assertEqual(missing.status_code, 404)

    def test_search_by_client_company(self):
        response = self.client.get(
            reverse("layouts:search"), {"q": "Ромашка", "status": ""}
        )
        self.assertEqual(len(response.context["layouts"]), 3)

    def test_overdue_excludes_approved_and_checks_date(self):
        response = self.client.get(
            reverse("layouts:overdue"), {"date": "2026-09-20"}
        )
        titles = [layout.title for layout in response.context["layouts"]]
        self.assertEqual(titles, ["Главная страница"])
        wrong = self.client.get(
            reverse("layouts:overdue"), {"date": "не-дата"}
        )
        self.assertIsNotNone(wrong.context["error"])

    def test_statistics_includes_designer_without_layouts(self):
        response = self.client.get(reverse("layouts:statistics"))
        counts = {
            designer.name: designer.layouts_count
            for designer in response.context["by_designer"]
        }
        self.assertEqual(counts["Петров Олег"], 0)
        self.assertEqual(response.context["totals"]["waiting_count"], 2)
        discussed = [item.title for item in response.context["discussed"]]
        self.assertEqual(discussed, ["Главная страница"])

    def test_comment_pages(self):
        comment = Comment.objects.first()
        self.assertEqual(
            self.client.get(reverse("comments:list")).status_code, 200
        )
        detail = self.client.get(
            reverse("comments:detail", args=[comment.pk])
        )
        self.assertContains(detail, comment.text)
