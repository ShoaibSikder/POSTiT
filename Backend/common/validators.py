import warnings
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_FORMATS = {
    "JPEG": {".jpg", ".jpeg"},
    "PNG": {".png"},
    "WEBP": {".webp"},
}
IMAGE_CONTENT_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


def validate_uploaded_image(upload):
    from moderation.models import SystemSetting
    from moderation.services import get_platform_limit

    max_image_size = get_platform_limit(SystemSetting.Key.MAX_IMAGE_SIZE_BYTES)
    if upload.size > max_image_size:
        raise ValidationError(
            "Image exceeds the configured maximum size of %(max_size)s bytes.",
            params={"max_size": max_image_size},
        )

    extension = Path(upload.name).suffix.lower()
    content_type = getattr(upload, "content_type", None)
    try:
        upload.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(upload) as image:
                image_format = image.format
                image.verify()
        upload.seek(0)
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        UnidentifiedImageError,
    ) as exc:
        upload.seek(0)
        raise ValidationError("Upload must be a valid, safe image file.") from exc

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError("Only JPEG, PNG, and WebP images are allowed.")
    if extension not in ALLOWED_IMAGE_FORMATS[image_format]:
        raise ValidationError("Image extension does not match its file content.")
    if content_type and content_type.lower() != IMAGE_CONTENT_TYPES[image_format]:
        raise ValidationError("Image content type does not match its file content.")
