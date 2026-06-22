from django.core.mail import send_mail
from django.conf import settings
from .models import Notification


def notify(recipient, title, message, notification_type='GENERAL', link='', send_email=True):
    """
    Create an in-system notification and optionally send an email.
    """
    Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
    )
    if send_email and recipient.email:
        try:
            send_mail(
                subject=f'[KUST CS PGMS] {title}',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=True,
            )
        except Exception:
            pass
