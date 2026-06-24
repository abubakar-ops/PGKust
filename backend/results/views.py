from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.permissions import IsAdmin, IsActiveStudent, IsActiveLecturer, IsPGCoordinator
from courses.models import Enrollment
from notifications.utils import notify
from .models import SemesterResultBatch, Result, SemesterGPA, CumulativeGPA
from .serializers import (
    ResultSerializer, ResultUploadSerializer, SemesterResultBatchSerializer,
    SemesterGPASerializer, CumulativeGPASerializer,
)


class StudentResultsView(APIView):
    """GET /api/results/mine/?session=<id>&semester=<FIRST|SECOND>"""
    permission_classes = [IsActiveStudent]

    def get(self, request):
        qs = Result.objects.filter(
            enrollment__student=request.user.student_profile,
            batch__status=SemesterResultBatch.Status.APPROVED,
        ).select_related(
            "enrollment__allocation__course", "batch__session"
        )
        session_id = request.query_params.get("session")
        semester = request.query_params.get("semester")
        if session_id:
            qs = qs.filter(batch__session_id=session_id)
        if semester:
            qs = qs.filter(batch__semester=semester)
        return Response(ResultSerializer(qs, many=True).data)


class StudentGPAView(APIView):
    """GET /api/results/gpa/  — returns all semester GPAs + cumulative."""
    permission_classes = [IsActiveStudent]

    def get(self, request):
        profile = request.user.student_profile
        semester_gpas = SemesterGPA.objects.filter(
            student=profile
        ).select_related("session").order_by("session__start_date", "semester")
        try:
            cgpa = CumulativeGPA.objects.get(student=profile)
            cgpa_data = CumulativeGPASerializer(cgpa).data
        except CumulativeGPA.DoesNotExist:
            cgpa_data = None
        return Response({
            "semester_gpas": SemesterGPASerializer(semester_gpas, many=True).data,
            "cumulative": cgpa_data,
        })


class LecturerResultUploadView(APIView):
    """POST /api/results/upload/  — lecturer uploads results for a batch."""
    permission_classes = [IsActiveLecturer]

    def post(self, request):
        batch_id = request.data.get("batch")
        results_data = request.data.get("results", [])

        try:
            batch = SemesterResultBatch.objects.get(pk=batch_id)
        except SemesterResultBatch.DoesNotExist:
            return Response({"detail": "Batch not found."}, status=404)

        if batch.status == SemesterResultBatch.Status.APPROVED:
            return Response({"detail": "Cannot modify an approved batch."}, status=400)

        errors = []
        created = 0
        with transaction.atomic():
            for item in results_data:
                s = ResultUploadSerializer(data=item)
                if not s.is_valid():
                    errors.append({"enrollment": item.get("enrollment"), "errors": s.errors})
                    continue
                d = s.validated_data
                try:
                    enrollment = Enrollment.objects.get(pk=d["enrollment"])
                except Enrollment.DoesNotExist:
                    errors.append({"enrollment": d["enrollment"], "errors": "Enrollment not found."})
                    continue
                Result.objects.update_or_create(
                    enrollment=enrollment,
                    defaults={"score": d["score"], "batch": batch}
                )
                created += 1

        return Response({"uploaded": created, "errors": errors}, status=200)


class BatchListView(APIView):
    """GET /api/results/batches/  — list all result batches."""
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = SemesterResultBatch.objects.all().select_related("session", "approved_by__user")
        s = request.query_params.get("status")
        if s:
            qs = qs.filter(status=s)
        return Response(SemesterResultBatchSerializer(qs, many=True).data)

    def post(self, request):
        serializer = SemesterResultBatchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class ApproveBatchView(APIView):
    """POST /api/results/batches/<pk>/approve/  — PG Coordinator approves batch."""
    permission_classes = [IsPGCoordinator]

    def post(self, request, pk):
        try:
            batch = SemesterResultBatch.objects.get(pk=pk)
        except SemesterResultBatch.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        action = request.data.get("action")
        comment = request.data.get("comment", "")
        if action == "approve":
            from django.utils import timezone
            batch.status = SemesterResultBatch.Status.APPROVED
            batch.coordinator_comment = comment
            batch.approved_at = timezone.now()
            batch.approved_by = request.user.admin_profile
            batch.save()
            # Notify all affected students
            results = Result.objects.filter(batch=batch).select_related(
                "enrollment__student__user"
            )
            for r in results:
                notify(
                    r.enrollment.student.user,
                    "Results Published",
                    f"Your {batch.semester} semester {batch.session.name} results are now available.",
                    "RESULT",
                )
            return Response({"detail": "Batch approved and students notified."})
        elif action == "reject":
            batch.status = SemesterResultBatch.Status.REJECTED
            batch.coordinator_comment = comment
            batch.save()
            return Response({"detail": "Batch rejected."})
        return Response({"detail": "Invalid action."}, status=400)
