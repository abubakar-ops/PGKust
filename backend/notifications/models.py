from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import CustomUser


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        REGISTRATION = 'REGISTRATION', _('Registration')
        ENROLLMENT = 'ENROLLMENT', _('Course Enrollment')
        RESULT = 'RESULT', _('Results')
        APR = 'APR', _('Annual Progress Report')
        FEE = 'FEE', _('Fee Payment')
        MATERIAL = 'MATERIAL', _('Course Material')
        GENERAL = 'GENERAL', _('General')

    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=15, choices=NotificationType.choices, default=NotificationType.GENERAL)
    title = models.CharField(max_length=150)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, help_text='Optional URL to redirect on click')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')

    def __str__(self):
        read_status = 'Read' if self.is_read else 'Unread'
        return f'[{read_status}] {self.recipient.email}: {self.title}'

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
