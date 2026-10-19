from django.urls import reverse
from rest_framework import serializers
from .models import FeePayment


class FeePaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    # Receipts are not publicly served; point at the authenticated download view.
    receipt_file = serializers.SerializerMethodField()

    class Meta:
        model = FeePayment
        fields = [
            "id", "student", "student_name", "academic_year", "amount",
            "payment_method", "status", "transaction_reference",
            "receipt_file", "rejection_reason", "approved_at", "created_at",
        ]
        read_only_fields = [
            "id", "student", "student_name", "status", "approved_at", "created_at",
        ]

    def get_student_name(self, obj):
        return obj.student.user.get_full_name()

    def get_receipt_file(self, obj):
        if not obj.receipt_file:
            return None
        return reverse("fees:receipt_download", args=[obj.pk])
