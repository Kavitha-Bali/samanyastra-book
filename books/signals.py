import os
from io import BytesIO

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from django.conf import settings
from PIL import Image

from .models import Books

THUMBNAIL_SIZE    = (300, 400)
THUMBNAIL_QUALITY = 82


def build_thumbnail(book):
    """
    Generate and save a compressed thumbnail for the given Books instance.
    Reads the source image from local MEDIA_ROOT (works for both local dev
    and production where files are synced to disk before processing).
    Returns True on success, False on failure.
    Always overwrites any existing thumbnail.
    """
    if not book.cover_image:
        return False

    # Try local filesystem first (always works in dev; works in prod if
    # MEDIA_ROOT is populated). Falls back to storage backend open().
    local_path = os.path.join(settings.MEDIA_ROOT, book.cover_image.name)

    try:
        if os.path.exists(local_path):
            with open(local_path, 'rb') as f:
                img_bytes = BytesIO(f.read())
        else:
            # Production: file lives only in Azure — read all bytes into memory
            book.cover_image.open('rb')
            img_bytes = BytesIO(book.cover_image.read())
            book.cover_image.close()
        img = Image.open(img_bytes)
        img.load()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"build_thumbnail failed for book {book.pk}: {e}")
        return False

    # Normalise to RGB for JPEG output
    if img.mode in ('RGBA', 'LA', 'PA'):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=THUMBNAIL_QUALITY, optimize=True)
    buffer.seek(0)

    thumb_filename = _thumb_filename(book.cover_image.name)

    if book.cover_thumbnail:
        try:
            book.cover_thumbnail.delete(save=False)
        except Exception:
            pass

    book.cover_thumbnail.save(
        thumb_filename,
        ContentFile(buffer.read()),
        save=True,
    )
    return True


@receiver(post_save, sender=Books)
def generate_cover_thumbnail(sender, instance, **kwargs):
    """Fire async Celery task to generate thumbnail whenever a book is saved with a cover."""
    if not instance.cover_image:
        return
    if instance.cover_thumbnail:
        return
    from .tasks import generate_thumbnail_task
    generate_thumbnail_task.delay(instance.pk)


def _thumb_filename(original_name):
    base = os.path.basename(original_name)
    name, _ = os.path.splitext(base)
    return f"{name}_thumb.jpg"
