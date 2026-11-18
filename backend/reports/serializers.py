from rest_framework import serializers
from .models import AnnualProgressReport


class APRSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    supervisor_name = serializers.SerializerMethodField()
    session_name = serializers.CharField(source="session.name", read_only=True)

    class Meta:
        model = AnnualProgressReport
        fields = [
            "id", "student", "student_name", "session", "session_name",
            "year_of_study", "research_progress", "training_activities",
            "publications", "issues_concerns", "next_year_plan",
            "status", "submitted_at",
            "supervisor_comments", "supervisor_endorsed_at",
            "coordinator_comments", "coordinator_approved_at",
            "progression_cleared",
        ]
        read_only_fields = [
            "id", "student", "student_name", "session_name",
            "supervisor_name", "status", "submitted_at",
            "supervisor_endorsed_at", "coordinator_approved_at",
            "progression_cleared",
        ]

    def get_student_name(self, obj):
        return obj.student.user.get_full_name()

    def get_supervisor_name(self, obj):
        if obj.student.supervisor:
            return obj.student.supervisor.user.get_full_name()
        return None
