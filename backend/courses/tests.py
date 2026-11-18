from datetime import date
import tempfile

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import clear_url_caches, resolve, reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from accounts.models import CustomUser, LecturerProfile, StudentProfile
from fees.models import FeePayment
from pgms import urls as project_urls
from results.models import SemesterResultBatch
from .models import (
    AcademicSession, Course, CourseAllocation, CourseMaterial, Programme,
    Enrollment, Timetable,
)


class TimetableAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.session = AcademicSession.objects.create(
            name="2025/2026", is_current=True,
            department_fee="1000.00",
            start_date=date(2025, 10, 1), end_date=date(2026, 7, 31),
        )
        self.programme = Programme.objects.create(
            name="Computer Science", programme_type="MSC", duration_years=2,
        )
        self.course = Course.objects.create(
            code="CSC701", title="Advanced Computing", credit_units=3,
            semester="FIRST", programme=self.programme,
        )
        self.other_course = Course.objects.create(
            code="CSC702", title="Research Methods", credit_units=3,
            semester="FIRST", programme=self.programme,
        )
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            email="admin@example.com", password="test-password", role="ADMIN",
            first_name="Admin", last_name="User",
        )
        lecturer_user = user_model.objects.create_user(
            email="lecturer@example.com", password="test-password", role="LECTURER",
            first_name="Ada", last_name="Lecturer",
        )
        student_user = user_model.objects.create_user(
            email="student@example.com", password="test-password", role="STUDENT",
            first_name="Stu", last_name="Dent",
        )
        other_lecturer_user = user_model.objects.create_user(
            email="other@example.com", password="test-password", role="LECTURER",
            first_name="Other", last_name="Lecturer",
        )
        self.lecturer = LecturerProfile.objects.create(
            user=lecturer_user, staff_id="L001", status="ACTIVE",
        )
        self.other_lecturer = LecturerProfile.objects.create(
            user=other_lecturer_user, staff_id="L002", status="ACTIVE",
        )
        self.student = StudentProfile.objects.create(
            user=student_user, programme="MSC", matric_number="M001",
            admission_year=2025, status="ACTIVE",
        )
        self.allocation = CourseAllocation.objects.create(
            lecturer=self.lecturer, course=self.course, session=self.session,
            semester="FIRST",
        )
        self.other_allocation = CourseAllocation.objects.create(
            lecturer=self.other_lecturer, course=self.other_course, session=self.session,
            semester="FIRST",
        )
        Enrollment.objects.create(
            student=self.student, allocation=self.allocation, status="APPROVED",
        )

    def test_admin_can_create_update_list_and_delete_timetable(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/courses/admin/timetable/", {
            "allocation": self.allocation.id, "day": "MON",
            "start_time": "09:00", "end_time": "11:00", "venue": "Room 1",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        timetable_id = response.data["id"]
        listed = self.client.get("/api/courses/admin/timetable/")
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.data), 1)
        updated = self.client.patch(
            f"/api/courses/admin/timetable/{timetable_id}/", {"venue": "Room 2"},
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["venue"], "Room 2")
        deleted = self.client.delete(f"/api/courses/admin/timetable/{timetable_id}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Timetable.objects.filter(pk=timetable_id).exists())

    def test_timetable_clash_is_rejected(self):
        self.client.force_authenticate(self.admin)
        payload = {
            "allocation": self.allocation.id, "day": "TUE",
            "start_time": "09:00", "end_time": "11:00", "venue": "Room 1",
        }
        self.assertEqual(
            self.client.post("/api/courses/admin/timetable/", payload).status_code,
            status.HTTP_201_CREATED,
        )
        payload["allocation"] = self.other_allocation.id
        payload["start_time"] = "10:00"
        self.assertEqual(
            self.client.post("/api/courses/admin/timetable/", payload).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_student_and_lecturer_receive_only_relevant_entries(self):
        Timetable.objects.create(
            allocation=self.allocation, day="MON",
            start_time="09:00", end_time="11:00", venue="Room 1",
        )
        Timetable.objects.create(
            allocation=self.other_allocation, day="TUE",
            start_time="09:00", end_time="11:00", venue="Room 2",
        )
        self.client.force_authenticate(self.student.user)
        student_response = self.client.get("/api/courses/timetable/")
        self.assertEqual(
            [item["allocation"] for item in student_response.data], [self.allocation.id]
        )
        self.client.force_authenticate(self.lecturer.user)
        lecturer_response = self.client.get("/api/courses/timetable/")
        self.assertEqual(
            [item["allocation"] for item in lecturer_response.data], [self.allocation.id]
        )

    def test_unauthenticated_user_cannot_view_or_manage_timetable(self):
        self.assertEqual(
            self.client.get("/api/courses/timetable/").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            self.client.post("/api/courses/admin/timetable/", {}).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_non_admin_cannot_manage_timetable(self):
        self.client.force_authenticate(self.lecturer.user)
        self.assertEqual(
            self.client.get("/api/courses/admin/timetable/").status_code,
            status.HTTP_403_FORBIDDEN,
        )


class CourseMaterialAPITests(TestCase):
    def setUp(self):
        self.media_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_directory.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_directory.name, DEBUG=True)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
        original_urlpatterns = project_urls.urlpatterns
        project_urls.urlpatterns = [
            pattern for pattern in original_urlpatterns
            if not str(pattern.pattern).startswith("^media/")
        ] + static(settings.MEDIA_URL, document_root=self.media_directory.name)
        clear_url_caches()

        def restore_urlpatterns():
            project_urls.urlpatterns = original_urlpatterns
            clear_url_caches()

        self.addCleanup(restore_urlpatterns)
        self.client = APIClient()
        self.session = AcademicSession.objects.create(
            name="2025/2026", is_current=True,
            department_fee="1000.00",
            start_date=date(2025, 10, 1), end_date=date(2026, 7, 31),
        )
        self.programme = Programme.objects.create(
            name="Computer Science", programme_type="MSC", duration_years=2,
        )
        self.course = Course.objects.create(
            code="CSC803", title="Distributed Systems", credit_units=3,
            semester="FIRST", programme=self.programme,
        )
        user_model = get_user_model()
        lecturer_user = user_model.objects.create_user(
            email="lecturer2@example.com", password="test-password", role="LECTURER",
            first_name="Ada", last_name="Lecturer",
        )
        enrolled_user = user_model.objects.create_user(
            email="enrolled@example.com", password="test-password", role="STUDENT",
            first_name="Enrolled", last_name="Student",
        )
        unenrolled_user = user_model.objects.create_user(
            email="unenrolled@example.com", password="test-password", role="STUDENT",
            first_name="Unenrolled", last_name="Student",
        )
        self.lecturer = LecturerProfile.objects.create(
            user=lecturer_user, staff_id="L010", status="ACTIVE",
        )
        other_lecturer_user = user_model.objects.create_user(
            email="other-lecturer@example.com", password="test-password-123", role="LECTURER",
            first_name="Other", last_name="Lecturer",
        )
        self.other_lecturer = LecturerProfile.objects.create(
            user=other_lecturer_user, staff_id="L011", status="ACTIVE",
        )
        self.enrolled_student = StudentProfile.objects.create(
            user=enrolled_user, programme="MSC", matric_number="M010",
            admission_year=2025, status="ACTIVE",
        )
        self.unenrolled_student = StudentProfile.objects.create(
            user=unenrolled_user, programme="MSC", matric_number="M011",
            admission_year=2025, status="ACTIVE",
        )
        self.allocation = CourseAllocation.objects.create(
            lecturer=self.lecturer, course=self.course, session=self.session,
            semester="FIRST",
        )
        Enrollment.objects.create(
            student=self.enrolled_student, allocation=self.allocation, status="APPROVED",
        )
        self.material = CourseMaterial.objects.create(
            allocation=self.allocation, uploader=self.lecturer, title="Lecture Notes 1",
            file=SimpleUploadedFile("notes.pdf", b"%PDF-1.4 test", content_type="application/pdf"),
        )
        self.other_course = Course.objects.create(
            code="CSC804", title="Other Course", credit_units=3,
            semester=Course.Semester.FIRST, programme=self.programme,
        )
        self.other_allocation = CourseAllocation.objects.create(
            lecturer=self.other_lecturer, course=self.other_course, session=self.session,
            semester=Course.Semester.FIRST,
        )
        self.other_material = CourseMaterial.objects.create(
            allocation=self.other_allocation, uploader=self.other_lecturer,
            title="Other Lecturer Material",
            file=SimpleUploadedFile("other.pdf", b"%PDF-other", content_type="application/pdf"),
        )

    def test_enrolled_student_sees_material_without_fee_payment(self):
        self.assertFalse(FeePayment.objects.filter(student=self.enrolled_student).exists())
        self.client.force_authenticate(self.enrolled_student.user)
        response = self.client.get(f"/api/courses/materials/{self.allocation.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Lecture Notes 1")
        self.assertEqual(response.data[0]["course_code"], "CSC803")
        self.assertTrue(response.data[0]["file_available"])
        self.assertFalse(response.data[0]["can_delete"])

    def test_unenrolled_student_cannot_see_material(self):
        self.client.force_authenticate(self.unenrolled_student.user)
        response = self.client.get(f"/api/courses/materials/{self.allocation.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "You are not enrolled in this course.")

    def test_rejected_fee_payment_does_not_block_access(self):
        FeePayment.objects.create(
            student=self.enrolled_student, academic_year=self.session.name,
            amount=1000, payment_method="MANUAL", status="REJECTED",
        )
        self.client.force_authenticate(self.enrolled_student.user)
        response = self.client.get(f"/api/courses/materials/{self.allocation.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_access_materials(self):
        response = self.client.get(f"/api/courses/materials/{self.allocation.id}/")
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_lecturer_can_still_upload_material(self):
        self.client.force_authenticate(self.lecturer.user)
        upload = SimpleUploadedFile(
            "slides.pdf", b"%PDF-1.4 more test content", content_type="application/pdf"
        )
        response = self.client.post(
            f"/api/courses/materials/{self.allocation.id}/upload/",
            {"title": "Week 2 Slides", "file": upload},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Week 2 Slides")
        material = CourseMaterial.objects.get(allocation=self.allocation, title="Week 2 Slides")
        self.assertEqual(response.data["file"], material.file.url)
        self.assertTrue(material.file.storage.exists(material.file.name))
        with material.file.open("rb") as stored_file:
            self.assertEqual(stored_file.read(), b"%PDF-1.4 more test content")
        retrieved = self.client.get(f"/api/courses/materials/{self.allocation.id}/")
        self.assertEqual(retrieved.status_code, status.HTTP_200_OK)
        returned_material = next(item for item in retrieved.data if item["id"] == material.id)
        self.assertTrue(returned_material["file_available"])
        self.assertEqual(returned_material["file"], response.data["file"])

        media_response = self.client.get(response.data["file"])
        media_route = resolve(response.data["file"])
        self.assertEqual(media_response.status_code, status.HTTP_200_OK, media_route.kwargs)
        try:
            self.assertEqual(
                b"".join(media_response.streaming_content),
                b"%PDF-1.4 more test content",
            )
        finally:
            media_response.close()

    def test_missing_stored_file_is_reported_without_deleting_material_record(self):
        self.material.file.storage.delete(self.material.file.name)
        self.client.force_authenticate(self.enrolled_student.user)
        response = self.client.get(f"/api/courses/materials/{self.allocation.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertFalse(response.data[0]["can_delete"])
        self.assertFalse(response.data[0]["file_available"])
        self.assertTrue(CourseMaterial.objects.filter(pk=self.material.pk).exists())

    def test_recent_materials_only_includes_allowed_allocations(self):
        self.client.force_authenticate(self.enrolled_student.user)
        response = self.client.get("/api/courses/materials/recent/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.material.id)
        self.client.force_authenticate(self.unenrolled_student.user)
        response = self.client.get("/api/courses/materials/recent/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_lecturer_can_see_own_allocation_material(self):
        self.client.force_authenticate(self.lecturer.user)
        response = self.client.get(f"/api/courses/materials/{self.allocation.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertTrue(response.data[0]["can_delete"])

    def test_lecturer_can_delete_own_material_and_file(self):
        self.client.force_authenticate(self.lecturer.user)
        file_name = self.material.file.name
        file_storage = self.material.file.storage
        response = self.client.delete(
            f"/api/courses/materials/{self.allocation.id}/{self.material.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CourseMaterial.objects.filter(pk=self.material.pk).exists())
        self.assertFalse(file_storage.exists(file_name))

    def test_lecturer_cannot_delete_another_lecturers_material(self):
        self.client.force_authenticate(self.lecturer.user)
        response = self.client.delete(
            f"/api/courses/materials/{self.other_allocation.id}/{self.other_material.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(CourseMaterial.objects.filter(pk=self.other_material.pk).exists())
        self.assertTrue(self.other_material.file.storage.exists(self.other_material.file.name))

    def test_unauthenticated_user_cannot_delete_material(self):
        response = self.client.delete(
            f"/api/courses/materials/{self.allocation.id}/{self.material.id}/"
        )
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
        self.assertTrue(CourseMaterial.objects.filter(pk=self.material.pk).exists())

    def test_student_cannot_delete_material(self):
        self.client.force_authenticate(self.enrolled_student.user)
        response = self.client.delete(
            f"/api/courses/materials/{self.allocation.id}/{self.material.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(CourseMaterial.objects.filter(pk=self.material.pk).exists())

    def test_lecturer_can_delete_material_when_file_is_already_missing(self):
        self.material.file.storage.delete(self.material.file.name)
        self.client.force_authenticate(self.lecturer.user)
        response = self.client.delete(
            f"/api/courses/materials/{self.allocation.id}/{self.material.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CourseMaterial.objects.filter(pk=self.material.pk).exists())

    def test_deleted_material_is_absent_from_student_lists_and_dashboard_materials(self):
        self.client.force_authenticate(self.lecturer.user)
        response = self.client.delete(
            f"/api/courses/materials/{self.allocation.id}/{self.material.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.client.force_authenticate(self.enrolled_student.user)
        listed = self.client.get(f"/api/courses/materials/{self.allocation.id}/")
        recent = self.client.get("/api/courses/materials/recent/")
        self.assertEqual(listed.data, [])
        self.assertEqual(recent.data, [])

    def test_upload_records_authenticated_lecturer_as_uploader(self):
        self.client.force_authenticate(self.lecturer.user)
        upload = SimpleUploadedFile("owned.pdf", b"%PDF-owned", content_type="application/pdf")
        response = self.client.post(
            f"/api/courses/materials/{self.allocation.id}/upload/",
            {"file": upload},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            CourseMaterial.objects.get(pk=response.data["id"]).uploader_id,
            self.lecturer.id,
        )


class AdminAcademicCrudTests(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            email="academic-admin@example.com",
            password="test-password",
            role=CustomUser.Role.ADMIN,
        )
        self.student_user = CustomUser.objects.create_user(
            email="academic-student@example.com",
            password="test-password",
            role=CustomUser.Role.STUDENT,
        )
        self.lecturer_user = CustomUser.objects.create_user(
            email="academic-lecturer@example.com",
            password="test-password",
            role=CustomUser.Role.LECTURER,
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            programme=StudentProfile.Programme.MSC,
            matric_number="ADUST/PG/TEST/001",
            admission_year=2026,
            status=StudentProfile.Status.ACTIVE,
        )
        self.lecturer = LecturerProfile.objects.create(
            user=self.lecturer_user,
            staff_id="STAFF-TEST-001",
            status=LecturerProfile.Status.ACTIVE,
        )
        self.client.force_authenticate(user=self.admin)
        self.sessions_url = reverse("courses:admin_session_list")
        self.programmes_url = reverse("courses:admin_programme_list")
        self.courses_url = reverse("courses:admin_course_list")

    def create_session(self, **overrides):
        data = {
            "name": "2026/2027",
            "start_date": "2026-09-01",
            "end_date": "2027-07-31",
            "department_fee": "1000.00",
            "is_current": False,
        }
        data.update(overrides)
        return AcademicSession.objects.create(**data)

    def create_programme(self, **overrides):
        data = {
            "name": "Computer Science",
            "programme_type": Programme.ProgrammeType.MSC,
            "duration_years": 2,
        }
        data.update(overrides)
        return Programme.objects.create(**data)

    def test_admin_can_create_read_update_and_delete_all_academic_records(self):
        session_response = self.client.post(self.sessions_url, {
            "name": "2026/2027",
            "start_date": "2026-09-01",
            "end_date": "2027-07-31",
            "department_fee": "1000.00",
            "is_current": True,
        }, format="json")
        self.assertEqual(session_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(session_response.data["department_fee"], "1000.00")
        session_id = session_response.data["id"]
        self.assertEqual(self.client.get(self.sessions_url).data[0]["name"], "2026/2027")
        self.assertEqual(
            self.client.get(reverse("courses:admin_session_detail", args=[session_id])).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(self.client.patch(
            reverse("courses:admin_session_detail", args=[session_id]),
            {"name": "2026/2028"},
            format="json",
        ).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.delete(
            reverse("courses:admin_session_detail", args=[session_id])
        ).status_code, status.HTTP_204_NO_CONTENT)

        programme_response = self.client.post(self.programmes_url, {
            "name": "Computer Science",
            "programme_type": "MSC",
            "duration_years": 2,
            "description": "Postgraduate computing programme",
        }, format="json")
        self.assertEqual(programme_response.status_code, status.HTTP_201_CREATED)
        programme_id = programme_response.data["id"]
        self.assertEqual(self.client.get(self.programmes_url).data[0]["description"],
                         "Postgraduate computing programme")
        self.assertEqual(self.client.patch(
            reverse("courses:admin_programme_detail", args=[programme_id]),
            {"duration_years": 3},
            format="json",
        ).status_code, status.HTTP_200_OK)

        course_response = self.client.post(self.courses_url, {
            "code": "csc801",
            "title": "Advanced Computing",
            "credit_units": 3,
            "semester": "FIRST",
            "programme": programme_id,
            "is_elective": False,
            "is_active": True,
            "description": "Graduate-level course",
        }, format="json")
        self.assertEqual(course_response.status_code, status.HTTP_201_CREATED)
        course_id = course_response.data["id"]
        self.assertEqual(course_response.data["code"], "CSC801")
        self.assertEqual(course_response.data["programme_name"], "Computer Science")
        self.assertEqual(self.client.get(self.courses_url).data[0]["title"], "Advanced Computing")
        self.assertEqual(self.client.patch(
            reverse("courses:admin_course_detail", args=[course_id]),
            {"title": "Advanced Computing II"},
            format="json",
        ).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.delete(
            reverse("courses:admin_course_detail", args=[course_id])
        ).status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.delete(
            reverse("courses:admin_programme_detail", args=[programme_id])
        ).status_code, status.HTTP_204_NO_CONTENT)

    def test_students_and_lecturers_cannot_access_any_admin_crud_operation(self):
        session = self.create_session()
        programme = self.create_programme()
        course = Course.objects.create(
            code="CSC801",
            title="Advanced Computing",
            credit_units=3,
            semester=Course.Semester.FIRST,
            programme=programme,
        )
        routes = (
            (self.sessions_url, reverse("courses:admin_session_detail", args=[session.pk])),
            (self.programmes_url, reverse("courses:admin_programme_detail", args=[programme.pk])),
            (self.courses_url, reverse("courses:admin_course_detail", args=[course.pk])),
        )
        for user in (self.student_user, self.lecturer_user):
            self.client.force_authenticate(user=user)
            for collection_url, detail_url in routes:
                self.assertEqual(self.client.get(collection_url).status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(self.client.post(collection_url, {}, format="json").status_code,
                                 status.HTTP_403_FORBIDDEN)
                self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(self.client.patch(detail_url, {}, format="json").status_code,
                                 status.HTTP_403_FORBIDDEN)
                self.assertEqual(self.client.delete(detail_url).status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_required_duplicate_and_non_positive_inputs_are_rejected(self):
        self.assertEqual(self.client.post(self.sessions_url, {}, format="json").status_code,
                         status.HTTP_400_BAD_REQUEST)
        missing_fee = self.client.post(self.sessions_url, {
            "name": "2026/2027",
            "start_date": "2026-09-01",
            "end_date": "2027-07-31",
        }, format="json")
        self.assertEqual(missing_fee.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("department_fee", missing_fee.data["errors"])

        for invalid_fee in ("not-a-number", "-1.00", "1.001"):
            invalid_fee_response = self.client.post(self.sessions_url, {
                "name": "2026/2027",
                "start_date": "2026-09-01",
                "end_date": "2027-07-31",
                "department_fee": invalid_fee,
            }, format="json")
            self.assertEqual(invalid_fee_response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_dates = self.client.post(self.sessions_url, {
            "name": "2026/2027",
            "start_date": "2027-01-01",
            "end_date": "2026-12-31",
            "department_fee": "1000.00",
        }, format="json")
        self.assertEqual(invalid_dates.status_code, status.HTTP_400_BAD_REQUEST)
        self.create_session()
        duplicate_session = self.client.post(self.sessions_url, {
            "name": "2026/2027",
            "start_date": "2026-09-01",
            "end_date": "2027-07-31",
            "department_fee": "1000.00",
        }, format="json")
        self.assertEqual(duplicate_session.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", duplicate_session.data["errors"])

    def test_concurrent_duplicate_session_name_integrity_error_is_validation_response(self):
        from django.db import IntegrityError
        from unittest.mock import patch

        for error_message in (
            "UNIQUE constraint failed: courses_academicsession.name",
            "UNIQUE constraint failed: index 'unique_academic_session_name_ci'",
        ):
            with self.subTest(error_message=error_message), patch(
                "courses.views.AcademicSessionSerializer.save",
                side_effect=IntegrityError(error_message),
            ):
                response = self.client.post(self.sessions_url, {
                    "name": "2026/2027",
                    "start_date": "2026-09-01",
                    "end_date": "2027-07-31",
                    "department_fee": "1000.00",
                }, format="json")

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("name", response.data["errors"])

        self.assertEqual(self.client.post(self.programmes_url, {
            "name": "Invalid Duration",
            "programme_type": "MSC",
            "duration_years": 0,
        }, format="json").status_code, status.HTTP_400_BAD_REQUEST)
        self.create_programme()
        duplicate_programme = self.client.post(self.programmes_url, {
            "name": "computer science",
            "programme_type": "MSC",
            "duration_years": 2,
        }, format="json")
        self.assertEqual(duplicate_programme.status_code, status.HTTP_400_BAD_REQUEST)

        programme = Programme.objects.get(name="Computer Science")
        invalid_course = self.client.post(self.courses_url, {
            "code": "CSC801",
            "title": "Advanced Computing",
            "credit_units": 0,
            "semester": "FIRST",
            "programme": programme.pk,
        }, format="json")
        self.assertEqual(invalid_course.status_code, status.HTTP_400_BAD_REQUEST)
        Course.objects.create(
            code="CSC801",
            title="Advanced Computing",
            credit_units=3,
            semester=Course.Semester.FIRST,
            programme=programme,
        )
        duplicate_course = self.client.post(self.courses_url, {
            "code": "csc801",
            "title": "Different title",
            "credit_units": 3,
            "semester": "FIRST",
            "programme": programme.pk,
        }, format="json")
        self.assertEqual(duplicate_course.status_code, status.HTTP_400_BAD_REQUEST)

    def test_referenced_records_cannot_be_deleted_or_cascade_academic_history(self):
        session = self.create_session(is_current=True)
        programme = self.create_programme()
        course = Course.objects.create(
            code="CSC801",
            title="Advanced Computing",
            credit_units=3,
            semester=Course.Semester.FIRST,
            programme=programme,
        )
        allocation = CourseAllocation.objects.create(
            lecturer=self.lecturer,
            course=course,
            session=session,
            semester=Course.Semester.FIRST,
        )
        enrollment = Enrollment.objects.create(
            student=self.student,
            allocation=allocation,
            status=Enrollment.Status.APPROVED,
        )
        result_batch = SemesterResultBatch.objects.create(
            session=session,
            semester=Course.Semester.FIRST,
            programme_type=Programme.ProgrammeType.MSC,
        )

        session_delete = self.client.delete(reverse("courses:admin_session_detail", args=[session.pk]))
        self.assertEqual(session_delete.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("referenced", session_delete.data["detail"])
        self.assertTrue(AcademicSession.objects.filter(pk=session.pk).exists())
        self.assertTrue(SemesterResultBatch.objects.filter(pk=result_batch.pk).exists())
        self.assertTrue(Enrollment.objects.filter(pk=enrollment.pk).exists())

        FeePayment.objects.create(
            student=self.student,
            academic_year=session.name,
            amount="100.00",
            payment_method=FeePayment.PaymentMethod.MANUAL,
        )
        rename_response = self.client.patch(
            reverse("courses:admin_session_detail", args=[session.pk]),
            {"name": "2026/2028"},
            format="json",
        )
        self.assertEqual(rename_response.status_code, status.HTTP_200_OK)
        self.assertTrue(FeePayment.objects.filter(academic_year="2026/2028").exists())
        session_delete = self.client.delete(reverse("courses:admin_session_detail", args=[session.pk]))
        self.assertEqual(session_delete.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("fee payments", session_delete.data["detail"])

        programme_delete = self.client.delete(reverse("courses:admin_programme_detail", args=[programme.pk]))
        self.assertEqual(programme_delete.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Programme.objects.filter(pk=programme.pk).exists())
        self.assertTrue(Course.objects.filter(pk=course.pk).exists())

        course_delete = self.client.delete(reverse("courses:admin_course_detail", args=[course.pk]))
        self.assertEqual(course_delete.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Course.objects.filter(pk=course.pk).exists())
        self.assertTrue(CourseAllocation.objects.filter(pk=allocation.pk).exists())
