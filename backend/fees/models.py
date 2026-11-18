from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import StudentProfile


def receipt_upload_path(instance, filename):
    return f'fee_receipts/{instance.academic_year}/{instance.student.matric_number}/{filename}'


class FeePayment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')

    class PaymentMethod(models.TextChoices):
        ONLINE = 'ONLINE', _('Online (Paystack)')
        MANUAL = 'MANUAL', _('Manual (Bank Receipt Upload)')

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='fee_payments')
    academic_year = models.CharField(max_length=9, help_text='e.g. 2024/2025')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=6, choices=PaymentMethod.choices)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)

    # Online payment fields
    transaction_reference = models.CharField(max_length=100, blank=True, unique=True, null=True)
    paystack_payment_id = models.CharField(max_length=100, blank=True)

    # Manual payment fields
    receipt_file = models.FileField(upload_to=receipt_upload_path, blank=True, null=True)
    rejection_reason = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_fee_payments'
    )

    class Meta:
        unique_together = ('student', 'academic_year')
        ordering = ['-created_at']
        verbose_name = _('Fee Payment')
        verbose_name_plural = _('Fee Payments')

    def __str__(self):
        return f'{self.student.matric_number} | {self.academic_year} | {self.status}'

    @property
    def is_cleared(self):
        return self.status == self.Status.APPROVED
