"""Проверки форм, статусов, CSRF и файлов в отдельной тестовой базе."""
import tempfile
from datetime import timedelta
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import Client as HttpClient
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from layouts.forms import LayoutFilterForm, LayoutForm
from layouts.models import Layout
from participants.models import Client, Designer


def uploaded_image(name="preview.png", image_format="PNG"):
    data = BytesIO()
    Image.new("RGB", (40, 30), "white").save(data, format=image_format)
    return SimpleUploadedFile(name, data.getvalue(), content_type="image/png")


class Pr11FormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media = cls.enterClassContext(tempfile.TemporaryDirectory())
        cls.enterClassContext(override_settings(MEDIA_ROOT=cls.media))

    @classmethod
    def setUpTestData(cls):
        cls.designer = Designer.objects.create(
            name="Дизайнер", email="d11@example.com")
        cls.customer = Client.objects.create(
            name="Клиент", email="c11@example.com")
        cls.today = timezone.localdate()
        cls.layout = Layout.objects.create(
            title="Текущий макет", designer=cls.designer, client=cls.customer,
            sent_date=cls.today, approval_days=7,
        )

    def data(self, **overrides):
        data = {
            "title": "Новый макет", "designer": self.designer.pk,
            "client": self.customer.pk, "sent_date": self.today.isoformat(),
            "approval_days": 7,
        }
        data.update(overrides)
        return data

    def test_get_create_has_initial_date_and_explicit_fields(self):
        response = self.client.get(reverse("layouts:create"))
        form = response.context["form"]
        self.assertFalse(form.is_bound)
        self.assertEqual(form.initial["sent_date"], self.today)
        self.assertEqual(set(form.fields), {
            "title", "designer", "client", "sent_date",
            "approval_days", "image",
        })
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_valid_create_redirects_and_ignores_internal_fields(self):
        response = self.client.post(reverse("layouts:create"), self.data(
            title="  Новый   макет  ", status="APPROVED",
            version=99, slug="forged",
        ))
        obj = Layout.objects.get(title="Новый макет")
        self.assertRedirects(response, obj.get_absolute_url())
        self.assertEqual(obj.status, Layout.Status.REVIEW)
        self.assertEqual(obj.version, 1)
        self.assertNotEqual(obj.slug, "forged")
        self.assertEqual(obj.deadline, self.today + timedelta(days=7))

    def test_empty_post_is_bound_and_does_not_create(self):
        response = self.client.post(reverse("layouts:create"), {})
        self.assertTrue(response.context["form"].is_bound)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Layout.objects.count(), 1)

    def test_invalid_date_and_duration_keep_input_and_do_not_save(self):
        response = self.client.post(reverse("layouts:create"), self.data(
            sent_date=(self.today - timedelta(days=1)).isoformat(),
            approval_days=0,
        ))
        form = response.context["form"]
        self.assertIn("sent_date", form.errors)
        self.assertIn("approval_days", form.errors)
        self.assertEqual(form["title"].value(), "Новый макет")
        self.assertEqual(Layout.objects.count(), 1)

    def test_custom_title_and_image_validation(self):
        form = LayoutForm(self.data(title=" x "))
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)
        form = LayoutForm(self.data(), {"image": SimpleUploadedFile(
            "fake.jpg", b"not an image", content_type="image/jpeg",
        )})
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)
        form = LayoutForm(
            self.data(), {"image": uploaded_image("fake.jpg", "GIF")})
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)

    def test_image_size_is_limited(self):
        upload = uploaded_image()
        upload = SimpleUploadedFile(
            "large.png", upload.read() + b"0" * (5 * 1024 * 1024),
            content_type="image/png",
        )
        form = LayoutForm(self.data(), {"image": upload})
        self.assertFalse(form.is_valid())
        self.assertIn("5 МБ", str(form.errors["image"]))

    def test_duplicate_active_request_is_non_field_error(self):
        response = self.client.post(reverse("layouts:create"), self.data(
            title=self.layout.title,
        ))
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertContains(response, "Активная заявка на этот макет")
        self.assertEqual(Layout.objects.count(), 1)

    def test_database_also_prevents_active_duplicate(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Layout.objects.create(
                title=self.layout.title, designer=self.designer,
                client=self.customer, sent_date=self.today, approval_days=5,
            )

    def test_update_keeps_identity_and_does_not_conflict_with_itself(self):
        slug = self.layout.slug
        response = self.client.post(
            reverse("layouts:update", args=[self.layout.pk]),
            self.data(title=self.layout.title, approval_days=10),
        )
        self.layout.refresh_from_db()
        self.assertRedirects(response, self.layout.get_absolute_url())
        self.assertEqual(Layout.objects.count(), 1)
        self.assertEqual(self.layout.slug, slug)
        self.assertEqual(self.layout.deadline, self.today + timedelta(days=10))

    def test_update_conflict_is_rejected(self):
        other = Layout.objects.create(
            title="Другая заявка", designer=self.designer,
            client=self.customer,
            sent_date=self.today, approval_days=4,
        )
        response = self.client.post(reverse("layouts:update", args=[other.pk]),
                                    self.data(title=self.layout.title))
        self.assertTrue(response.context["form"].non_field_errors())
        other.refresh_from_db()
        self.assertEqual(other.title, "Другая заявка")

    def test_historical_record_can_keep_its_old_date_but_not_change_to_past(
            self):
        self.layout.sent_date = self.today - timedelta(days=10)
        self.layout.save()
        form = LayoutForm(self.data(title=self.layout.title,
                          sent_date=self.layout.sent_date.isoformat()),
                          instance=self.layout)
        self.assertTrue(form.is_valid(), form.errors)
        old_date = (self.today - timedelta(days=1)).isoformat()
        form = LayoutForm(self.data(sent_date=old_date),
                          instance=Layout.objects.get(pk=self.layout.pk))
        self.assertFalse(form.is_valid())
        self.assertIn("sent_date", form.errors)

    def test_cancel_keeps_history_and_releases_duplicate_conditions(self):
        response = self.client.post(
            reverse("layouts:cancel", args=[self.layout.pk]))
        self.layout.refresh_from_db()
        self.assertRedirects(response, self.layout.get_absolute_url())
        self.assertEqual(self.layout.status, Layout.Status.CANCELLED)
        self.assertEqual(Layout.objects.count(), 1)
        self.assertFalse(Layout.objects.active().exists())
        response = self.client.post(reverse("layouts:create"), self.data(
            title=self.layout.title,
        ))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Layout.objects.count(), 2)

    def test_cancel_get_is_405_and_does_not_change_data(self):
        response = self.client.get(
            reverse("layouts:cancel", args=[self.layout.pk]))
        self.assertEqual(response.status_code, 405)
        self.layout.refresh_from_db()
        self.assertEqual(self.layout.status, Layout.Status.REVIEW)

    def test_finished_records_and_missing_ids_cannot_be_edited_or_cancelled(
            self):
        self.layout.cancel()
        for pk in (self.layout.pk, 999999):
            self.assertEqual(self.client.get(
                reverse("layouts:update", args=[pk])).status_code, 404)
            self.assertEqual(self.client.post(
                reverse("layouts:cancel", args=[pk])).status_code, 404)
        self.layout.status = Layout.Status.APPROVED
        self.layout.save(update_fields=["status"])
        self.assertEqual(self.client.get(
            reverse("layouts:update", args=[self.layout.pk])).status_code, 404)

    def test_csrf_protects_create_edit_and_cancel(self):
        browser = HttpClient(enforce_csrf_checks=True)
        for url in (reverse("layouts:create"),
                    reverse("layouts:update", args=[self.layout.pk]),
                    reverse("layouts:cancel", args=[self.layout.pk])):
            self.assertEqual(browser.post(url, self.data()).status_code, 403)
        browser.get(reverse("layouts:create"))
        data = self.data(
            csrfmiddlewaretoken=browser.cookies["csrftoken"].value)
        self.assertEqual(browser.post(
            reverse("layouts:create"), data).status_code, 302)

    def test_filter_form_produces_models_and_date(self):
        form = LayoutFilterForm({"designer": self.designer.pk,
                                 "date": self.today.isoformat()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["designer"], self.designer)
        self.assertEqual(form.cleaned_data["date"], self.today)

    def test_invalid_filter_shows_errors_without_broadening_results(self):
        for params in ({"date": "not-a-date"}, {"designer": "999999"},
                       {"status": "fake"}, {"sort": "password"}):
            response = self.client.get(reverse("layouts:list"), params)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["filter_form"].errors)
            self.assertEqual(response.context["total"], 0)

    def test_filter_and_sort_survive_pagination_after_create(self):
        for index in range(3):
            Layout.objects.create(
                title=f"Ещё макет {index}", designer=self.designer,
                client=self.customer, sent_date=self.today, approval_days=7,
            )
        response = self.client.get(reverse("layouts:list"), {
            "designer": self.designer.pk, "date": self.today.isoformat(),
            "sort": "title", "page": 2,
        })
        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertContains(response, "sort=title")
        self.assertContains(response, f"date={self.today.isoformat()}")

    def test_cancelled_is_not_active_overdue_or_waiting(self):
        self.layout.sent_date = self.today - timedelta(days=20)
        self.layout.save()
        self.layout.cancel()
        self.assertFalse(Layout.objects.overdue(self.today).exists())
        response = self.client.get(
            reverse("layouts:list"), {"active_only": "on"})
        self.assertEqual(response.context["total"], 0)
        stats = self.client.get(reverse("layouts:statistics"))
        self.assertEqual(stats.context["totals"]["waiting_count"], 0)
        self.assertContains(self.client.get(
            self.layout.get_absolute_url()), "Отменён")

    def test_image_upload_retention_replace_and_clear(self):
        data = self.data(image=uploaded_image())
        response = self.client.post(reverse("layouts:create"), data)
        obj = Layout.objects.get(title="Новый макет")
        first = obj.image.name
        self.assertRedirects(response, obj.get_absolute_url())
        self.assertTrue(obj.image.storage.exists(first))
        self.assertContains(self.client.get(
            obj.get_absolute_url()), obj.image.url)
        self.client.post(reverse("layouts:update", args=[obj.pk]), self.data())
        obj.refresh_from_db()
        self.assertEqual(obj.image.name, first)
        self.client.post(reverse("layouts:update", args=[obj.pk]), self.data(
            image=uploaded_image("replacement.jpg", "JPEG"),
        ))
        obj.refresh_from_db()
        self.assertNotEqual(obj.image.name, first)
        self.client.post(reverse("layouts:update", args=[
                         obj.pk]), self.data(**{"image-clear": "on"}))
        obj.refresh_from_db()
        self.assertFalse(obj.image)

    def test_admin_can_upload_and_replace_image(self):
        admin = get_user_model().objects.create_superuser(
            "admin11", "a11@example.com", "test-password")
        self.client.force_login(admin)
        url = reverse("admin:layouts_layout_change", args=[self.layout.pk])
        data = self.data(title=self.layout.title, version=1,
                         status=Layout.Status.REVIEW,
                         image=uploaded_image(), **{
                             "comments-TOTAL_FORMS": 0,
                             "comments-INITIAL_FORMS": 0,
                             "comments-MIN_NUM_FORMS": 0,
                             "comments-MAX_NUM_FORMS": 1000,
                         })
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.layout.refresh_from_db()
        first = self.layout.image.name
        data["image"] = uploaded_image("admin-new.jpg", "JPEG")
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.layout.refresh_from_db()
        self.assertNotEqual(first, self.layout.image.name)
