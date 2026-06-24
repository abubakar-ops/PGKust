from decimal import Decimal
from rest_framework import serializers
from .models import SemesterResultBatch, Result, SemesterGPA, CumulativeGPA


class ResultSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="enrollment.allocation.course.code", read_only=True)
    course_title = serializers.CharField(source="enrollment.allocation.course.title", read_only=True)
    credit_units = serializers.IntegerField(source="enrollment.allocation.course.credit_units", read_only=True)

    class Meta:
        model = Result
        fields = ["id", "enrollment", "course_code", "course_title",
                  "credit_units", "score", "grade", "grade_point", "batch"]
        read_only_fields = ["id", "grade", "grade_point"]


class ResultUploadSerializer(serializers.Serializer):
    enrollment = serializers.IntegerField()
    score = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100"))


class SemesterResultBatchSerializer(serializers.ModelSerializer):
    session_name = serializers.CharField(source="session.name", read_only=True)
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = SemesterResultBatch
        fields = ["id", "session", "session_name", "semester", "programme_type",
                  "status", "coordinator_comment", "approved_at", "approved_by",
                  "approved_by_name", "created_at"]
        read_only_fields = ["id", "session_name", "approved_by_name", "created_at"]

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.user.get_full_name()
        return None


class SemesterGPASerializer(serializers.ModelSerializer):
    credit_units_earned = serializers.IntegerField(source="total_credit_units", read_only=True)

    class Meta:
        model = SemesterGPA
        fields = ["id", "session", "semester", "gpa", "credit_units_earned"]


class CumulativeGPASerializer(serializers.ModelSerializer):
    classification = serializers.CharField(read_only=True)

    class Meta:
        model = CumulativeGPA
        fields = ["id", "cgpa", "classification", "total_credit_units_earned", "total_quality_points"]
