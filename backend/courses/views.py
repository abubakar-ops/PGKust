import os
import logging
from django.conf import settings
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.http import FileResponse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from accounts.permissions import IsAdmin, IsActiveStudent, IsActiveLecturer
from notifications.utils import notify
from fees.models import FeePayment
from .models import AcademicSession, Programme, Course, CourseAllocation, Timetable, Enrollment, CourseMaterial
from .serializers import (
    AcademicSessionSerializer, ProgrammeSerializer, CourseSerializer, CourseAllocationSerializer,
    TimetableSerializer, EnrollmentSerializer, CourseMaterialSerializer,
    AvailableAllocationSerializer,
)

logger = logging.getLogger(__name__)


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
                student=request.user.student_profile, allocation__session=session, status="APPROVED"
            ).select_related("allocation__course", "allocation__lecturer__user")
            allocation_ids = [e.allocation_id for e in enrollments]
        elif request.user.is_lecturer:
            allocations = CourseAllocation.objects.filter(
                lecturer=request.user.lecturer_profile, session=session
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

        profile = request.user.student_profile
        if Enrollment.objects.filter(student=profile, allocation=allocation).exists():
            return Response({"detail": "Already enrolled."}, status=400)

        enrollment = Enrollment.objects.create(
            student=profile, allocation=allocation, status=Enrollment.Status.PENDING
        )
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StudentEnrollmentListView(APIView):
    permission_classes = [IsActiveStudent]

    def get(self, request):
        qs = Enrollment.objects.filter(
            student=request.user.student_profile
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
            lecturer=request.user.lecturer_profile, session=session
        ).select_related("course", "session")
        return Response(CourseAllocationSerializer(qs, many=True).data)


class AvailableAllocationsView(APIView):
    """GET /api/courses/available/  — allocations in the current session a student can enroll in."""
    permission_classes = [IsActiveStudent]

    def get(self, request):
        try:
            session = AcademicSession.objects.get(is_current=True)
        except AcademicSession.DoesNotExist:
            return Response([])
        qs = CourseAllocation.objects.filter(session=session).select_related(
            "course", "session", "lecturer__user"
        )
        enrolled_allocation_ids = set(
            Enrollment.objects.filter(student=request.user.student_profile)
            .values_list("allocation_id", flat=True)
        )
        serializer = AvailableAllocationSerializer(
            qs, many=True, context={"enrolled_allocation_ids": enrolled_allocation_ids}
        )
        return Response(serializer.data)


class MaterialUploadView(APIView):
    permission_classes = [IsActiveLecturer]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, allocation_pk):
        try:
            allocation = CourseAllocation.objects.get(
                pk=allocation_pk, lecturer=request.user.lecturer_profile
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
            uploader=request.user.lecturer_profile,
            title=request.data.get("title", upload.name),
            file=upload,
        )
        if not material.file or not material.file.storage.exists(material.file.name):
            return Response(
                {"detail": "The uploaded file was not saved to media storage. Please retry the upload."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            CourseMaterialSerializer(
                material,
                context={"lecturer_profile_id": request.user.lecturer_profile.id},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class MaterialDeleteView(APIView):
    permission_classes = [IsActiveLecturer]

    def delete(self, request, allocation_pk, material_pk):
        try:
            material = CourseMaterial.objects.select_related("uploader").get(pk=material_pk)
        except CourseMaterial.DoesNotExist:
            return Response({"detail": "Material not found."}, status=status.HTTP_404_NOT_FOUND)

        if material.uploader_id != request.user.lecturer_profile.id:
            return Response(
                {"detail": "You can only delete materials that you uploaded."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if material.allocation_id != allocation_pk:
            return Response({"detail": "Material not found."}, status=status.HTTP_404_NOT_FOUND)

        storage = material.file.storage
        file_name = material.file.name
        try:
            with transaction.atomic():
                material.delete()
                if file_name and storage.exists(file_name):
                    storage.delete(file_name)
                    if storage.exists(file_name):
                        raise OSError("The uploaded file could not be removed from storage.")
        except (DatabaseError, OSError):
            logger.exception(
                "Failed to delete course material %s and its uploaded file.", material_pk
            )
            return Response(
                {"detail": "The material could not be deleted. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class MaterialListView(APIView):
    def get(self, request, allocation_pk):
        try:
            allocation = CourseAllocation.objects.get(pk=allocation_pk)
        except CourseAllocation.DoesNotExist:
            return Response({"detail": "Allocation not found."}, status=404)

        if request.user.is_student:
            profile = getattr(request.user, "student_profile", None)
            if profile is None or not profile.is_active:
                return Response({"detail": "Your student profile is not active."}, status=403)
            if not Enrollment.objects.filter(
                student=profile, allocation=allocation, status="APPROVED"
            ).exists():
                return Response({"detail": "You are not enrolled in this course."}, status=403)
        elif request.user.is_lecturer:
            lecturer = getattr(request.user, "lecturer_profile", None)
            if lecturer is None or not lecturer.is_active or allocation.lecturer_id != lecturer.id:
                return Response({"detail": "You are not the lecturer for this course."}, status=403)

        materials = CourseMaterial.objects.filter(allocation=allocation)
        lecturer_profile = getattr(request.user, "lecturer_profile", None)
        return Response(
            CourseMaterialSerializer(
                materials,
                many=True,
                context={
                    "lecturer_profile_id": getattr(lecturer_profile, "id", None),
                },
            ).data
        )


class StudentRecentMaterialsView(APIView):
    """GET /api/courses/materials/recent/ — a few most-recently uploaded materials
    across all of the student's approved enrollments. Reuses the same access rule
    as MaterialListView (approved enrollment only; no fee/session registration
    requirement)."""
    permission_classes = [IsActiveStudent]

    def get(self, request):
        profile = request.user.student_profile

        allowed_allocation_ids = Enrollment.objects.filter(
            student=profile, status="APPROVED"
        ).values_list("allocation_id", flat=True)

        try:
            limit = int(request.query_params.get("limit", 5))
        except ValueError:
            limit = 5

        materials = (
            CourseMaterial.objects.filter(allocation_id__in=allowed_allocation_ids)
            .select_related("allocation__course")
            .order_by("-uploaded_at")[:limit]
        )
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


class AdminAcademicListCreateView(ListCreateAPIView):
    permission_classes = [IsAdmin]
    pagination_class = None


class AdminAcademicDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdmin]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        blocker = self.get_external_deletion_blocker(instance)
        if blocker:
            return Response({"detail": blocker}, status=status.HTTP_409_CONFLICT)
        try:
            self.perform_destroy(instance)
        except ProtectedError as exc:
            references = sorted({
                str(obj._meta.verbose_name_plural) for obj in exc.protected_objects
            })
            detail = "Cannot delete this record while it is referenced"
            if references:
                detail += " by " + ", ".join(references)
            return Response({"detail": detail + "."}, status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_external_deletion_blocker(self, instance):
        return None


class AdminAcademicSessionListCreateView(AdminAcademicListCreateView):
    queryset = AcademicSession.objects.all()
    serializer_class = AcademicSessionSerializer

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError as exc:
            cause = exc.__cause__
            constraint_name = getattr(getattr(cause, "diag", None), "constraint_name", None)
            error_message = str(exc).lower()
            sqlite_name_conflict = "unique constraint failed" in error_message and (
                "courses_academicsession.name" in error_message
                or "unique_academic_session_name_ci" in error_message
            )
            if constraint_name in {
                "courses_academicsession_name_key",
                "unique_academic_session_name_ci",
            } or sqlite_name_conflict:
                raise ValidationError({
                    "name": "An academic session with this name already exists."
                }) from exc
            raise


class AdminAcademicSessionDetailView(AdminAcademicDetailView):
    queryset = AcademicSession.objects.all()
    serializer_class = AcademicSessionSerializer

    def get_external_deletion_blocker(self, instance):
        if FeePayment.objects.filter(academic_year=instance.name).exists():
            return "Cannot delete this academic session because fee payments refer to it."
        return None

    def perform_update(self, serializer):
        old_name = serializer.instance.name
        new_name = serializer.validated_data.get("name", old_name)
        with transaction.atomic():
            if old_name != new_name:
                student_ids = FeePayment.objects.filter(
                    academic_year=old_name
                ).values_list("student_id", flat=True)
                if FeePayment.objects.filter(
                    academic_year=new_name, student_id__in=student_ids
                ).exists():
                    raise ValidationError({
                        "name": "This name conflicts with existing fee payments for one or more students."
                    })
            instance = serializer.save()
            if old_name != instance.name:
                FeePayment.objects.filter(academic_year=old_name).update(
                    academic_year=instance.name
                )


class AdminProgrammeListCreateView(AdminAcademicListCreateView):
    queryset = Programme.objects.all()
    serializer_class = ProgrammeSerializer


class AdminProgrammeDetailView(AdminAcademicDetailView):
    queryset = Programme.objects.all()
    serializer_class = ProgrammeSerializer


class AdminCourseListCreateView(AdminAcademicListCreateView):
    queryset = Course.objects.select_related("programme")
    serializer_class = CourseSerializer


class AdminCourseDetailView(AdminAcademicDetailView):
    queryset = Course.objects.select_related("programme")
    serializer_class = CourseSerializer


class AdminAllocationListView(APIView):
    """GET /api/courses/admin/allocations/  — all allocations, optional ?session=<id> filter.
    Defaults to the current academic session when no filter is given.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        session_param = request.query_params.get("session")
        qs = CourseAllocation.objects.select_related("course", "session", "lecturer__user")
        if session_param:
            qs = qs.filter(session_id=session_param)
        else:
            try:
                current = AcademicSession.objects.get(is_current=True)
                qs = qs.filter(session=current)
            except AcademicSession.DoesNotExist:
                pass
        return Response(CourseAllocationSerializer(qs, many=True).data)


class AdminTimetableCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Timetable.objects.select_related(
            "allocation__course__programme",
            "allocation__lecturer__user",
            "allocation__session",
        )
        session_param = request.query_params.get("session")
        if session_param:
            qs = qs.filter(allocation__session_id=session_param)
        return Response(TimetableSerializer(qs, many=True).data)

    def post(self, request):
        serializer = TimetableSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=400)


class AdminTimetableDetailView(APIView):
    permission_classes = [IsAdmin]

    def get_object(self, pk):
        try:
            return Timetable.objects.select_related(
                "allocation__course__programme",
                "allocation__lecturer__user",
                "allocation__session",
            ).get(pk=pk)
        except Timetable.DoesNotExist:
            return None

    def patch(self, request, pk):
        timetable = self.get_object(pk)
        if timetable is None:
            return Response({"detail": "Not found."}, status=404)
        serializer = TimetableSerializer(timetable, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        timetable = self.get_object(pk)
        if timetable is None:
            return Response({"detail": "Not found."}, status=404)
        timetable.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminEnrollmentListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Enrollment.objects.filter(status=Enrollment.Status.PENDING).select_related(
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
            enrollment.status = Enrollment.Status.APPROVED
            enrollment.save()
            notify(enrollment.student.user, "Enrollment Approved",
                   f"Your enrollment in {enrollment.allocation.course.title} has been approved.",
                   "ENROLLMENT")
            return Response({"detail": "Enrollment approved."})
        elif action == "reject":
            enrollment.status = Enrollment.Status.REJECTED
            enrollment.save()
            notify(enrollment.student.user, "Enrollment Rejected",
                   f"Your enrollment in {enrollment.allocation.course.title} was not approved.",
                   "ENROLLMENT")
            return Response({"detail": "Enrollment rejected."})
        return Response({"detail": "Invalid action."}, status=400)
