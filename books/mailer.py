import logging

import requests
from django.conf import settings
from django.template import Context, Template

from django_messaging.models import MailTemplateMaster, OutBounds
from django_messaging.utils import get_object_or_none

logger = logging.getLogger(__name__)


def send_via_mail_service(to_email, subject, body, from_email=None, is_html=True):
    """POST a single email to the mail service. Returns True/False."""
    try:
        response = requests.post(
            f"{settings.MAIL_SERVICE_URL}/api/send-mail/",
            headers={"X-App-Secret": settings.MAIL_SERVICE_APP_SECRET},
            data={
                "app_id": settings.MAIL_SERVICE_APP_ID,
                "from_email": from_email or settings.MAIL_SERVICE_FROM_EMAIL,
                "to_email": to_email,
                "subject": subject,
                "body": body,
                "is_html": is_html,
            },
        )
    except requests.RequestException:
        logger.exception("Mail service request failed for %s", to_email)
        return False

    if not response.ok:
        logger.error(
            "Mail service returned %s for %s: %s",
            response.status_code, to_email, response.text,
        )
        return False
    return True


def send_email(template_name, *to_mail, **context):
    mail_template = get_object_or_none(MailTemplateMaster, name=template_name)

    if mail_template is None:
        raise ValueError("Invalid mail template given")

    subject   = mail_template.subject
    from_mail = mail_template.from_mail
    template  = Template(mail_template.template)
    mail_body = template.render(Context(context))

    results = [
        send_via_mail_service(recipient, subject, mail_body, from_email=from_mail)
        for recipient in to_mail
    ]

    OutBounds.objects.bulk_create([
        OutBounds(mail_template=mail_template, to_mail=recipient, body=mail_body, is_sent=sent)
        for recipient, sent in zip(to_mail, results)
    ])

    return all(results)
