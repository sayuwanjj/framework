"""Проверки пользовательских форм и защиты операций ПР11."""
import tempfile
from datetime import timedelta
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client as Browser
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from layouts.forms import LayoutForm
from layouts.models import Layout
from participants.models import Client, Designer


class Pr11FormTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.d = Designer.objects.create(name='Дизайнер', email='d11@test.ru')
        self.c = Client.objects.create(name='Клиент', email='c11@test.ru')
        self.data = dict(title='Тестовый макет', designer=self.d.pk,
                         client=self.c.pk, approval_days=7,
                         sent_date=timezone.localdate().isoformat())

    def create(self):
        form = LayoutForm(self.data)
        self.assertTrue(form.is_valid(), form.errors)
        return form.save()

    def test_create_redirects_and_ignores_internal_fields(self):
        response = self.client.post(reverse('layouts:create'), dict(
            self.data, status='APPROVED', version=99))
        obj = Layout.objects.get()
        self.assertRedirects(response, obj.get_absolute_url())
        self.assertEqual(obj.status, Layout.Status.REVIEW)
        self.assertEqual(obj.version, 1)

    def test_past_date_and_invalid_duration(self):
        data = dict(self.data, approval_days=0,
                    sent_date=(timezone.localdate() - timedelta(days=1)))
        form = LayoutForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('sent_date', form.errors)
        self.assertIn('approval_days', form.errors)
        self.assertFalse(Layout.objects.exists())

    def test_duplicate_rejected_and_cancel_releases_conditions(self):
        obj = self.create()
        form = LayoutForm(self.data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())
        obj.cancel()
        self.assertTrue(LayoutForm(self.data).is_valid())
        self.assertEqual(Layout.objects.count(), 1)

    def test_edit_does_not_conflict_with_itself(self):
        obj = self.create()
        form = LayoutForm(dict(self.data, approval_days=10), instance=obj)
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        self.assertEqual(saved.pk, obj.pk)
        self.assertEqual(Layout.objects.count(), 1)

    def test_get_cancel_is_405_and_post_preserves_history(self):
        obj = self.create()
        url = reverse('layouts:cancel', args=[obj.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 302)
        obj.refresh_from_db()
        self.assertEqual(obj.status, Layout.Status.CANCELLED)
        self.assertFalse(Layout.objects.active().exists())
        self.assertEqual(self.client.post(url).status_code, 404)

    def test_csrf_protects_create_edit_and_cancel(self):
        obj = self.create()
        browser = Browser(enforce_csrf_checks=True)
        for url in [reverse('layouts:create'),
                    reverse('layouts:update', args=[obj.pk]),
                    reverse('layouts:cancel', args=[obj.pk])]:
            self.assertEqual(browser.post(url, self.data).status_code, 403)

    def test_missing_and_inactive_edit_returns_404(self):
        self.assertEqual(self.client.get(
            reverse('layouts:update', args=[99999])).status_code, 404)
        obj = self.create()
        obj.cancel()
        self.assertEqual(self.client.get(
            reverse('layouts:update', args=[obj.pk])).status_code, 404)

    def test_bad_filter_does_not_broaden_selection(self):
        self.create()
        for data in [{'date': 'bad'}, {'designer': 99999}, {'sort': 'bad'}]:
            response = self.client.get(reverse('layouts:list'), data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['filter_form'].errors)
            self.assertEqual(response.context['total'], 0)

    def test_image_validation_and_upload(self):
        data = BytesIO()
        Image.new('RGB', (20, 20), 'white').save(data, 'PNG')
        upload = SimpleUploadedFile('preview.png', data.getvalue())
        form = LayoutForm(self.data, {'image': upload})
        self.assertTrue(form.is_valid(), form.errors)
        obj = form.save()
        self.assertTrue(obj.image.storage.exists(obj.image.name))
        self.assertContains(self.client.get(obj.get_absolute_url()),
                            obj.image.url)
        bad = LayoutForm(dict(self.data, title='Другой макет'),
                         {'image': SimpleUploadedFile('fake.png', b'bad')})
        self.assertFalse(bad.is_valid())
        self.assertIn('image', bad.errors)
