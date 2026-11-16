"""Переиспользуемые проверки загруженных изображений."""
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


def validate_layout_image(value):
    """Разрешить небольшие PNG, JPEG и WebP по содержимому файла."""
    if value.size > 5 * 1024 * 1024:
        raise ValidationError("Размер изображения не должен превышать 5 МБ.")
    try:
        value.open()
        position = value.tell()
        image = Image.open(value)
        if image.format not in {"PNG", "JPEG", "WEBP"}:
            raise ValidationError("Выберите изображение PNG, JPEG или WebP.")
        image.verify()
        value.seek(position)
    except (OSError, ValueError, UnidentifiedImageError) as error:
        raise ValidationError("Не удалось прочитать изображение.") from error
