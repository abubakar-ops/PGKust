import os
from django.conf import settings
from django.db import transaction
from django.http import FileResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from accounts.permissions import IsAdmin, IsActiveStudent, IsActiveLecturer
from notifications.utils import notify
from .models import AcademicSession, Course, CourseAllocation, Timetable, Enrollment, CourseMaterial
from .serializers import (
    AcademicSessionSerializer, CourseSerializer, CourseAllocationSerializer,
    TimetableSerializer, EnrollmentSerializer, CourseMaterialSerializer,
)


class CurrentSessionView(APIView):
    def get(self, request):
        try:
            session = AcademicSession.objects.get(is_current=True)
        except AcademicSession.DoesNotExist:
            return Response({"detail": "No active academic session."}, status=404)
        return Response(AcademicSessionSerializer(session).data)


class CourseListView(APIView):
    def get(self, request):
        qs = Course.objects.filter(is_active=True).select_related("programme")
        programme = request.query_params.get("programme")
        semester = request.query_params.get("semester")
        if programme:
            qs = qs.filter(programme__programme_type=programme)
        if semester:
            qs = qs.filter(semester=semester)
        return Response(CourseSerializer(qs, many=True).data)


class TimetableView(APIView):
    """Returns timetable for the current session for the requesting user."""

    def get(self, request):
        try:
            session = AcademicSession.objects.get(is_current=True)
        except AcademicSession.DoesNotExist:
            return Response([])

        if request.user.is_student:
            enrollments = Enrollment.objects.filter(
                student=request.user.studentprofile, allocation__session=session, status="APPROVED"
            ).select_related("allocation__course", "allocation__lecturer__user")
            allocation_ids = [e.allocation_id for e in enrollments]
        elif request.user.is_lecturer:
            allocations = CourseAllocation.objects.filter(
                lecturer=request.user.lecturerprofile, session=session
            )
            allocation_ids = [a.id for a in allocations]
        else:
            allocation_ids = CourseAllocation.objects.filter(
                session=session
            ).values_list("id", flat=True)

        timetable = Timetable.objects.filter(
            allocation_id__in=allocation_ids
        ).select_related("allocation__course", "allocation__lecturer__user")
        return Response(TimetableSerializer(timetable, many=True).data)


class EnrollView(APIView):
    """POST: student enrolls in a course allocation."""
    permission_classes = [IsActiveStudent]

    def post(self, request):
        allocation_id = request.data.get("allocation")
        try:
            allocation = CourseAllocation.objects.get(pk=allocation_id)
        except CourseAllocation.DoesNotExist:
            return Response({"detail": "Course allocation not found."}, status=404)

        profile = request.user.studentprofile
        if Enrollment.objects.filter(student=profile, allocation=allocation).exists():
            return Response({"detail": "Already enrolled."}, status=400)

        enrollment = Enrollment.objects.create(
            student=profile, allocation=allocation, status=Enrollment.PENDING
        )
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StudentEnrollmentListView(APIView):
    permission_classes = [IsActiveStudent]

    def get(self, request):
        qs = Enrollment.objects.filter(
            student=request.user.studentprofile
        ).select_related("allocation__course", "allocation__session", "allocation__lecturer__user")
        return Response(EnrollmentSerializer(qs, many=True).data)


class LecturerAllocationListView(APIView):
    permission_classes = [IsActiveLecturer]

    def get(self, request):
        try:
            session = AcademicSession.objects.get(is_current=True)
        except AcademicSession.DoesNotExist:
            return Response([])
        qs = CourseAllocation.objects.filter(
            lecturer=request.user.lecturerprofile, session=session
        ).select_related("course", "session")
        return Response(CourseAllocationSerializer(qs, many=True).data)


class MaterialUploadView(APIView):
    permission_classes = [IsActiveLecturer]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, allocation_pk):
        try:
            allocation = CourseAllocation.objects.get(
                pk=allocation_pk, lecturer=request.user.lecturerprofile
            )
        except CourseAllocation.DoesNotExist:
            return Response({"detail": "Allocation not found."}, status=404)

        upload = request.FILES.get("file")
        if not upload:
            return Response({"detail": "No file provided."}, status=400)

        ext = os.path.splitext(upload.name)[1].lower()
        if ext not in settings.ALLOWED_MATERIAL_EXTENSIONS:
            return Response({"detail": f"File type {ext} not allowed."}, status=400)
        if upload.size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            return Response({"detail": "File too large."}, status=400)

        material = CourseMaterial.objects.create(
            allocation=allocation,
            title=request.data.get("title", upload.name),
            file=upload,
        )
        return Response(CourseMaterialSerializer(material).data, status=status.HTTP_201_CREATED)


class MaterialListView(APIView):
    def get(self, request, allocation_pk):
        try:
            allocation = CourseAllocation.objects.get(pk=allocation_pk)
        except CourseAllocation.DoesNotExist:
            return Response({"detail": "Allocation not found."}, status=404)

        if request.user.is_student:
            if not Enrollment.objects.filter(
                student=request.user.studentprofile, allocation=allocation, status="APPROVED"
            ).exists():
                return Response({"detail": "Not enrolled."}, status=403)

        materials = CourseMaterial.objects.filter(allocation=allocation)
        return Response(CourseMaterialSerializer(materials, many=True).data)


# ── Admin views ──────────────────────────────────────────────────────────────

class AdminAllocateCourseView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = CourseAllocationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=400)


class AdminTimetableCreateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = TimetableSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=400)


class AdminEnrollmentListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Enrollment.objects.filter(status=Enrollment.PENDING).select_related(
            "student__user", "allocation__course", "allocation__session"
        )
        return Response(EnrollmentSerializer(qs, many=True).data)


class AdminApproveEnrollmentView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            enrollment = Enrollment.objects.select_related("student__user").get(pk=pk)
        except Enrollment.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        action = request.data.get("action")
        if action == "approve":
            enrollment.status = Enrollment.APPROVED
            enrollment.save()
            notify(enrollment.student.user, "Enrollment Approved",
                   f"Your enrollment in {enrollment.allocation.course.title} has been approved.",
                   "ENROLLMENT")
            return Response({"detail": "Enrollment approved."})
        elif action == "reject":
            enrollment.status = Enrollment.REJECTED
            enrollment.save()
            notify(enrollment.student.user, "Enrollment Rejected",
                   f"Your enrollment in {enrollment.allocation.course.title} was not approved.",
                   "ENROLLMENT")
            return Response({"detail": "Enrollment rejected."})
        return Response({"detail": "Invalid action."}, status=400)
