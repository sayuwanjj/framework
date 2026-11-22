"""Валидатор изображений пользовательской формы и Admin."""
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


def validate_layout_image(value):
    if value.size > 5 * 1024 * 1024:
        raise ValidationError('Допустимый размер изображения — до 5 МБ.')
    try:
        value.open()
        image = Image.open(value)
        if image.format not in {'PNG', 'JPEG', 'WEBP'}:
            raise ValidationError('Выберите PNG, JPEG или WebP.')
        image.verify()
        value.seek(0)
    except (OSError, ValueError, UnidentifiedImageError) as error:
        raise ValidationError('Не удалось прочитать изображение.') from error
