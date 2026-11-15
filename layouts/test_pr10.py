"""Регрессионные проверки административной панели и запросов ПР10."""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from layouts.models import Layout
from participants.models import Client, Designer


class Pr10Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.designer = Designer.objects.create(
            name="Дизайнер", email="d@example.com")
        cls.customer = Client.objects.create(
            name="Клиент", email="c@example.com")
        for i in range(6):
            Layout.objects.create(
                title=f"Макет {i}",
                designer=cls.designer,
                client=cls.customer,
                sent_date=date(2026, 9, 1),
                approval_days=5,
                status=(Layout.Status.APPROVED if i == 0
                        else Layout.Status.REVIEW),
            )
        cls.admin = get_user_model().objects.create_superuser(
            "testadmin", "a@example.com", "test-password")

    def test_admin_requires_login(self):
        self.assertEqual(self.client.get(
            '/admin/layouts/layout/').status_code, 302)

    def test_admin_search_filter_and_inlines(self):
        self.client.force_login(self.admin)
        response = self.client.get('/admin/layouts/layout/', {'q': 'Макет 0'})
        self.assertEqual(response.context['cl'].result_count, 1)
        response = self.client.get(
            '/admin/layouts/layout/',
            {'status__exact': Layout.Status.APPROVED},
        )
        self.assertEqual(response.context['cl'].result_count, 1)
        for model, obj in [('designer', self.designer),
                           ('client', self.customer)]:
            response = self.client.get(
                f'/admin/participants/{model}/{obj.pk}/change/')
            self.assertContains(response, 'Макет 0')

    def test_approved_layout_is_not_overdue(self):
        self.assertEqual(Layout.objects.overdue(date(2026, 9, 10)).count(), 5)
        obj = Layout.objects.filter(status=Layout.Status.REVIEW).first()
        obj.approve()
        self.assertEqual(Layout.objects.overdue(date(2026, 9, 10)).count(), 4)

    def test_partial_save_updates_derived_deadline(self):
        obj = Layout.objects.first()
        obj.approval_days = 10
        obj.save(update_fields=['approval_days'])
        obj.refresh_from_db()
        self.assertEqual(obj.deadline, date(2026, 9, 11))

    def test_related_objects_need_one_query(self):
        with self.assertNumQueries(1):
            for obj in Layout.objects.select_related('designer', 'client'):
                str(obj.designer)
                str(obj.client)

    def test_pagination_preserves_filter_and_sort(self):
        response = self.client.get(
            reverse('layouts:list'), {
                'designer': self.designer.pk, 'sort': 'title', 'page': 2})
        self.assertEqual(response.context['page_obj'].number, 2)
        self.assertContains(response, 'sort=title')
        self.assertContains(response, f'designer={self.designer.pk}')
