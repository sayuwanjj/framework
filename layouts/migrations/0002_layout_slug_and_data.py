from django.db import migrations, models
from django.utils.text import slugify


STATUS_MAP = {
    "На согласовании": "REVIEW",
    "На доработке": "REVISION",
    "Утверждён": "APPROVED",
}


def populate(apps, schema_editor):
    Layout = apps.get_model("layouts", "Layout")
    alias = schema_editor.connection.alias
    for obj in Layout.objects.using(alias).all().iterator():
        obj.slug = f"{slugify(obj.title)[:200] or 'layout'}-{obj.pk}"
        obj.status = STATUS_MAP.get(obj.status, obj.status)
        obj.save(using=alias, update_fields=["slug", "status"])


def reverse_status(apps, schema_editor):
    Layout = apps.get_model("layouts", "Layout")
    alias = schema_editor.connection.alias
    for label, code in STATUS_MAP.items():
        Layout.objects.using(alias).filter(status=code).update(status=label)


class Migration(migrations.Migration):
    dependencies = [("layouts", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="layout", name="slug",
            field=models.SlugField(max_length=250, null=True, blank=True,
                                   verbose_name="Адрес макета"),
        ),
        migrations.RunPython(populate, reverse_status),
        migrations.AlterField(
            model_name="layout", name="slug",
            field=models.SlugField(max_length=250, unique=True, blank=True,
                                   verbose_name="Адрес макета"),
        ),
        migrations.AlterField(
            model_name="layout", name="status",
            field=models.CharField(
                max_length=20, default="REVIEW", verbose_name="Статус",
                choices=[("REVIEW", "На согласовании"),
                         ("REVISION", "На доработке"),
                         ("APPROVED", "Утверждён")],
            ),
        ),
    ]
