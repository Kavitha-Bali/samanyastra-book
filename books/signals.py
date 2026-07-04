import os
from io import BytesIO

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from PIL import Image

from .models import Books

THUMBNAIL_SIZE    = (300, 400)
THUMBNAIL_QUALITY = 82


def build_thumbnail(book):
    """
    Generate and save a thumbnail for the given Books instance.
    Returns True on success, False on failure.
    Skips if the book has no cover_image.
    """
    if not book.cover_image:
        return False

    try:
        book.cover_image.open('rb')
        img = Image.open(book.cover_image)
        img.load()
        book.cover_image.close()
    except Exception:
        return False

    # Normalise to RGB for JPEG output
    if img.mode in ('RGBA', 'LA'):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    elif img.mode == 'P':
        img = img.convert('RGB')
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=THUMBNAIL_QUALITY, optimize=True)
    buffer.seek(0)

    thumb_filename = _thumb_filename(book.cover_image.name)

    # Delete old thumbnail file from storage if it exists
    if book.cover_thumbnail:
        try:
            book.cover_thumbnail.delete(save=False)
        except Exception:
            pass

    # Save the new file through Django's storage backend properly
    book.cover_thumbnail.save(
        thumb_filename,
        ContentFile(buffer.read()),
        save=True,          # calls book.save(update_fields=['cover_thumbnail'])
    )
    return True


@receiver(post_save, sender=Books)
def generate_cover_thumbnail(sender, instance, created, **kwargs):
    # Only auto-generate when cover_image is present and thumbnail is missing
    if not instance.cover_image:
        return
    if instance.cover_thumbnail and instance.cover_thumbnail.name.startswith('covers/thumbs/'):
        return
    # Disconnect signal temporarily to avoid recursion from the save() inside build_thumbnail
    post_save.disconnect(generate_cover_thumbnail, sender=Books)
    try:
        build_thumbnail(instance)
    finally:
        post_save.connect(generate_cover_thumbnail, sender=Books)


def _thumb_filename(original_name):
    base = os.path.basename(original_name)
    name, _ = os.path.splitext(base)
    return f"{name}_thumb.jpg"
