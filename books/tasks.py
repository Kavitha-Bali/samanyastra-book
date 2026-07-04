from celery import shared_task
from django.template import Context, Template

from django_messaging.models import MailTemplateMaster, OutBounds
from django_messaging.backends import OutlookBackend
from django_messaging.utils import get_object_or_none


@shared_task(bind=True)
def generate_thumbnail_task(self, book_id):
    """Celery task: generate compressed thumbnail for a book's cover image."""
    from .models import Books
    from .signals import build_thumbnail
    try:
        book = Books.objects.get(pk=book_id)
    except Books.DoesNotExist:
        return False
    # Clear existing thumbnail so build_thumbnail always overwrites
    if book.cover_thumbnail:
        try:
            book.cover_thumbnail.delete(save=True)
        except Exception:
            pass
        book.refresh_from_db()
    return build_thumbnail(book)


@shared_task(bind=True)
def send_email(self, template_name, *to_mail, **context):
    """Should not be called directly — use send_email.delay()"""

    mail_template = get_object_or_none(MailTemplateMaster, name=template_name)

    if mail_template is None:
        raise ValueError("Invalid mail template given")

    subject         = mail_template.subject
    from_mail       = mail_template.from_mail
    template_string = mail_template.template

    template  = Template(template_string)
    mail_body = template.render(Context(context))

    msg = OutlookBackend(subject, mail_body, from_mail, to_mail)
    msg.send()

    OutBounds.objects.create(
        mail_template=mail_template,
        to_mail=to_mail,
        body=mail_body,
    )
    return True
