from rest_framework import serializers
from .models import FeePayment


class FeePaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

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
