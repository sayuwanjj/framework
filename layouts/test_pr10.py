"""Регрессионные проверки административной панели и запросов ПР10."""
from datetime import date
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from comments.models import Comment
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

    def test_edit_action_opens_selected_record(self):
        self.client.force_login(self.admin)
        obj = Layout.objects.first()
        response = self.client.post('/admin/layouts/layout/', {
            'action': 'edit_selected', '_selected_action': [obj.pk],
            'index': '0',
        })
        self.assertRedirects(
            response, f'/admin/layouts/layout/{obj.pk}/change/')
        response = self.client.get('/admin/layouts/layout/')
        self.assertContains(response, 'Редактировать выбранную запись')
        self.assertContains(response, 'Выберите действие')
        self.assertNotContains(response, '---------')

    def test_edit_action_rejects_multiple_records(self):
        self.client.force_login(self.admin)
        selected = list(Layout.objects.values_list('pk', flat=True)[:2])
        response = self.client.post('/admin/layouts/layout/', {
            'action': 'edit_selected', '_selected_action': selected,
            'index': '0',
        }, follow=True)
        self.assertContains(
            response, 'Для редактирования выберите ровно одну запись.')

    def test_editor_group_can_change_titles_and_comments(self):
        call_command('setup_editor_group', stdout=StringIO())
        group = Group.objects.get(name='Редакторы сервиса')
        self.assertEqual(group.permissions.count(), 16)
        editor = get_user_model().objects.create_user(
            'editor', password='test-password', is_staff=True)
        editor.groups.add(group)
        self.assertFalse(editor.has_perm('auth.change_user'))
        self.client.force_login(editor)
        obj = Layout.objects.first()
        response = self.client.post(
            f'/admin/layouts/layout/{obj.pk}/change/', {
                'title': 'Изменено в админке', 'version': obj.version,
                'designer': self.designer.pk, 'client': self.customer.pk,
                'status': obj.status, 'sent_date': obj.sent_date.isoformat(),
                'approval_days': obj.approval_days,
                'comments-TOTAL_FORMS': 0, 'comments-INITIAL_FORMS': 0,
                'comments-MIN_NUM_FORMS': 0, 'comments-MAX_NUM_FORMS': 1000,
            })
        self.assertEqual(response.status_code, 302)
        obj.refresh_from_db()
        self.assertEqual(obj.title, 'Изменено в админке')
        comment = Comment.objects.create(
            layout=obj, author=self.customer, text='До изменения',
            comment_date=date(2026, 9, 1), layout_version=1)
        response = self.client.post(
            f'/admin/comments/comment/{comment.pk}/change/', {
                'layout': obj.pk, 'author': self.customer.pk,
                'text': 'После изменения', 'comment_date': '2026-09-01',
                'layout_version': 1,
            })
        self.assertEqual(response.status_code, 302)
        comment.refresh_from_db()
        self.assertEqual(comment.text, 'После изменения')
        response = self.client.get(
            f'/admin/participants/designer/{self.designer.pk}/change/')
        self.assertContains(response, 'name="layouts-0-title"')

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

    def test_slug_url_is_unique_and_stable(self):
        obj = Layout.objects.first()
        other = Layout.objects.last()
        other.title = obj.title
        other.save()
        self.assertNotEqual(obj.slug, other.slug)
        url = obj.get_absolute_url()
        self.assertContains(self.client.get(url), obj.title)
        obj.title = "Новое название"
        obj.save()
        self.assertEqual(obj.get_absolute_url(), url)
        self.assertEqual(self.client.get(
            reverse('layouts:detail_by_slug', args=['missing-slug'])
        ).status_code, 404)

    def test_database_recalculates_generated_field(self):
        obj = Layout.objects.first()
        Layout.objects.filter(pk=obj.pk).update(version=1)
        obj.refresh_from_db()
        self.assertFalse(obj.is_revised)
        Layout.objects.filter(pk=obj.pk).update(version=2)
        obj.refresh_from_db()
        self.assertTrue(obj.is_revised)

    def test_status_codes_have_russian_labels(self):
        obj = Layout.objects.first()
        obj.status = Layout.Status.APPROVED
        obj.save(update_fields=['status'])
        response = self.client.get(reverse('layouts:list'),
                                   {'status': 'APPROVED'})
        self.assertContains(response, 'Утверждён')
        self.assertEqual(obj.get_status_display(), 'Утверждён')

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
