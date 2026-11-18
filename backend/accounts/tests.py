from datetime import datetime, timedelta
from unittest.mock import patch
from urllib.parse import urlsplit

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from courses.models import AcademicSession, Course, CourseAllocation, Enrollment, Programme
from reports.models import AnnualProgressReport
from results.models import CumulativeGPA, Result, SemesterGPA, SemesterResultBatch
from .models import CustomUser, LecturerProfile, StudentProfile


class AdminAccountListTests(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            email='admin-list@example.com',
            password='test-password',
            role=CustomUser.Role.ADMIN,
        )
        self.student_user = CustomUser.objects.create_user(
            email='student-list@example.com',
            password='test-password',
            first_name='Amina',
            last_name='Pending',
            role=CustomUser.Role.STUDENT,
        )
        self.active_student_user = CustomUser.objects.create_user(
            email='active-student@example.com',
            password='test-password',
            first_name='Bala',
            last_name='Active',
            role=CustomUser.Role.STUDENT,
        )
        self.suspended_student_user = CustomUser.objects.create_user(
            email='suspended-student@example.com',
            password='test-password',
            first_name='Chika',
            last_name='Suspended',
            role=CustomUser.Role.STUDENT,
        )
        StudentProfile.objects.create(
            user=self.student_user,
            programme=StudentProfile.Programme.MSC,
            matric_number='MSC-PENDING-1',
            admission_year=2025,
            status=StudentProfile.Status.PENDING,
        )
        StudentProfile.objects.create(
            user=self.active_student_user,
            programme=StudentProfile.Programme.PHD,
            matric_number='PHD-ACTIVE-1',
            admission_year=2024,
            status=StudentProfile.Status.ACTIVE,
        )
        StudentProfile.objects.create(
            user=self.suspended_student_user,
            programme=StudentProfile.Programme.MSC,
            matric_number='MSC-SUSPENDED-1',
            admission_year=2023,
            status=StudentProfile.Status.SUSPENDED,
        )
        self.lecturer_user = CustomUser.objects.create_user(
            email='pending-lecturer@example.com',
            password='test-password',
            first_name='Danjuma',
            last_name='Pending',
            role=CustomUser.Role.LECTURER,
        )
        self.active_lecturer_user = CustomUser.objects.create_user(
            email='active-lecturer@example.com',
            password='test-password',
            first_name='Ene',
            last_name='Active',
            role=CustomUser.Role.LECTURER,
        )
        LecturerProfile.objects.create(
            user=self.lecturer_user,
            staff_id='STAFF-PENDING-1',
            status=LecturerProfile.Status.PENDING,
        )
        LecturerProfile.objects.create(
            user=self.active_lecturer_user,
            staff_id='STAFF-ACTIVE-1',
            specialization='Systems',
            is_supervisor=True,
            status=LecturerProfile.Status.ACTIVE,
        )
        self.students_url = reverse('accounts:all_students')
        self.pending_students_url = reverse('accounts:pending_students')
        self.lecturers_url = reverse('accounts:all_lecturers')
        self.pending_lecturers_url = reverse('accounts:pending_lecturers')

    def test_admin_all_lists_include_every_profile_status_without_private_data(self):
        self.client.force_authenticate(self.admin)

        students = self.client.get(self.students_url)
        self.assertEqual(students.status_code, status.HTTP_200_OK)
        self.assertEqual({item['status'] for item in students.data},
                         {'PENDING', 'ACTIVE', 'SUSPENDED'})
        self.assertEqual(len(students.data), 3)
        self.assertTrue({
            'email', 'first_name', 'last_name', 'full_name', 'matric_number',
            'programme', 'admission_year', 'status',
        }.issubset(students.data[0]))

        lecturers = self.client.get(self.lecturers_url)
        self.assertEqual(lecturers.status_code, status.HTTP_200_OK)
        self.assertEqual({item['status'] for item in lecturers.data}, {'PENDING', 'ACTIVE'})
        self.assertEqual(len(lecturers.data), 2)
        self.assertTrue({
            'email', 'first_name', 'last_name', 'full_name', 'staff_id',
            'specialization', 'is_supervisor', 'status',
        }.issubset(lecturers.data[0]))
        for item in [*students.data, *lecturers.data]:
            self.assertNotIn('password', item)
            self.assertNotIn('username', item)
            self.assertNotIn('is_superuser', item)
            self.assertNotIn('user_permissions', item)

    def test_pending_endpoints_remain_limited_to_pending_profiles(self):
        self.client.force_authenticate(self.admin)
        students = self.client.get(self.pending_students_url)
        lecturers = self.client.get(self.pending_lecturers_url)
        self.assertEqual([item['status'] for item in students.data], ['PENDING'])
        self.assertEqual([item['status'] for item in lecturers.data], ['PENDING'])

    def test_all_lists_support_status_filter_and_identifier_name_search(self):
        self.client.force_authenticate(self.admin)

        students = self.client.get(self.students_url, {'status': 'suspended'})
        self.assertEqual(students.status_code, status.HTTP_200_OK)
        self.assertEqual([item['matric_number'] for item in students.data], ['MSC-SUSPENDED-1'])
        self.assertEqual(
            self.client.get(self.students_url, {'search': 'active-student@'}).data[0]['full_name'],
            'Bala Active',
        )
        self.assertEqual(
            self.client.get(self.students_url, {'search': 'PHD-ACTIVE'}).data[0]['programme'],
            StudentProfile.Programme.PHD,
        )

        lecturers = self.client.get(self.lecturers_url, {'status': 'active'})
        self.assertEqual(lecturers.status_code, status.HTTP_200_OK)
        self.assertEqual([item['staff_id'] for item in lecturers.data], ['STAFF-ACTIVE-1'])
        self.assertEqual(
            self.client.get(self.lecturers_url, {'search': 'STAFF-PENDING'}).data[0]['full_name'],
            'Danjuma Pending',
        )
        self.assertEqual(
            self.client.get(self.lecturers_url, {'search': 'Ene Active'}).data[0]['staff_id'],
            'STAFF-ACTIVE-1',
        )

    def test_invalid_status_is_rejected_and_non_admins_cannot_list_all_profiles(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(
            self.client.get(self.students_url, {'status': 'UNKNOWN'}).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.client.get(self.lecturers_url, {'status': 'SUSPENDED'}).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        for user in (self.student_user, self.active_lecturer_user):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.students_url).status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(self.client.get(self.lecturers_url).status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.students_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(self.lecturers_url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_student_review_returns_supported_profile_and_academic_records(self):
        student = StudentProfile.objects.get(matric_number='PHD-ACTIVE-1')
        supervisor = LecturerProfile.objects.create(
            user=CustomUser.objects.create_user(
                email='supervisor@example.com',
                password='test-password',
                first_name='Fati',
                last_name='Supervisor',
                role=CustomUser.Role.LECTURER,
            ),
            staff_id='STAFF-SUPERVISOR',
            specialization='Research',
            is_supervisor=True,
            status=LecturerProfile.Status.ACTIVE,
        )
        student.supervisor = supervisor
        student.registration_note = 'Admission documents verified.'
        student.save()
        session = AcademicSession.objects.create(
            name='2025/2026',
            department_fee='1000.00',
            start_date='2025-09-01',
            end_date='2026-07-31',
            is_current=True,
        )
        programme = Programme.objects.create(name='Computer Science', programme_type='PHD')
        course = Course.objects.create(
            code='CSC901', title='Research Methods', credit_units=3,
            semester=Course.Semester.FIRST, programme=programme,
        )
        allocation = CourseAllocation.objects.create(
            lecturer=supervisor, course=course, session=session,
            semester=Course.Semester.FIRST,
        )
        enrollment = Enrollment.objects.create(
            student=student, allocation=allocation, status=Enrollment.Status.APPROVED,
        )
        batch = SemesterResultBatch.objects.create(
            session=session, semester=Course.Semester.FIRST,
            programme_type=Programme.ProgrammeType.PHD,
        )
        Result.objects.create(enrollment=enrollment, batch=batch, score='85.00')
        SemesterGPA.objects.create(
            student=student, session=session, semester=Course.Semester.FIRST,
            gpa='4.50', total_credit_units=3, total_quality_points=14,
        )
        CumulativeGPA.objects.create(
            student=student, cgpa='4.50', classification='Distinction',
            total_credit_units_earned=3, total_quality_points=14,
        )
        AnnualProgressReport.objects.create(
            student=student, session=session, year_of_study=1,
            research_progress='Progress made.',
            training_activities='Research seminar.',
            next_year_plan='Continue research.',
            status=AnnualProgressReport.Status.SUPERVISOR_ENDORSED,
        )

        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('accounts:admin_student_review', args=[student.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['programme_display'], 'Doctor of Philosophy (PhD)')
        self.assertEqual(response.data['registration_note'], 'Admission documents verified.')
        self.assertEqual(response.data['supervisor']['staff_id'], 'STAFF-SUPERVISOR')
        self.assertEqual(response.data['enrollments'][0]['course_code'], 'CSC901')
        self.assertEqual(response.data['enrollments'][0]['result']['grade'], 'A')
        self.assertEqual(response.data['semester_gpas'][0]['session_name'], '2025/2026')
        self.assertEqual(response.data['cumulative_gpa']['classification'], 'Distinction')
        self.assertEqual(response.data['annual_progress_reports'][0]['status'], 'SUPERVISOR_ENDORSED')
        self.assertNotIn('password', response.data)
        self.assertNotIn('research_progress', response.data['annual_progress_reports'][0])

    def test_student_review_endpoint_is_admin_only_and_handles_missing_student(self):
        student = StudentProfile.objects.get(matric_number='MSC-PENDING-1')
        url = reverse('accounts:admin_student_review', args=[student.pk])
        self.client.force_authenticate(self.student_user)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.active_lecturer_user)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(self.admin)
        self.assertEqual(
            self.client.get(reverse('accounts:admin_student_review', args=[999999])).status_code,
            status.HTTP_404_NOT_FOUND,
        )


class AccountSecurityAndProfileTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='account-owner@example.com',
            password='Current-Password-123!',
            first_name='Account',
            last_name='Owner',
            phone_number='08012345678',
            role=CustomUser.Role.STUDENT,
        )
        self.student = StudentProfile.objects.create(
            user=self.user,
            programme=StudentProfile.Programme.MSC,
            matric_number='MSC-OWNER-1',
            admission_year=2025,
            status=StudentProfile.Status.ACTIVE,
        )
        self.me_url = reverse('accounts:me')
        self.change_password_url = reverse('accounts:change_password')
        self.forgot_password_url = reverse('accounts:forgot_password')

    @override_settings(
        DEBUG=True,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        PASSWORD_RESET_FRONTEND_URL='https://pgms.example.test',
    )
    def test_forgot_password_sends_reset_link_without_disclosing_account_existence(self):
        existing = self.client.post(
            self.forgot_password_url, {'email': self.user.email}, format='json'
        )
        missing = self.client.post(
            self.forgot_password_url, {'email': 'not-registered@example.com'}, format='json'
        )
        self.assertEqual(existing.status_code, status.HTTP_200_OK)
        self.assertEqual(existing.data, missing.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        reset_link = next(
            line for line in mail.outbox[0].body.splitlines()
            if line.startswith('https://pgms.example.test/reset-password/')
        )
        self.assertNotIn(self.user.password, mail.outbox[0].body)

        uidb64, token = urlsplit(reset_link).path.rstrip('/').rsplit('/', 2)[-2:]
        reset = self.client.post(
            reverse(
                'accounts:reset_password',
                kwargs={'uidb64': uidb64, 'token': token},
            ),
            {
                'new_password': 'Reset-From-Email-123!',
                'confirm_password': 'Reset-From-Email-123!',
            },
            format='json',
        )
        self.assertEqual(reset.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Reset-From-Email-123!'))

    @override_settings(
        DEBUG=False,
        EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
        PASSWORD_RESET_FRONTEND_URL='http://localhost:5173',
    )
    def test_production_reset_does_not_print_tokens_to_console_email_backend(self):
        with self.assertLogs('accounts.views', level='ERROR'):
            response = self.client.post(
                self.forgot_password_url,
                {'email': self.user.email},
                format='json',
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('email delivery is configured', response.data['detail'])

    def _reset_url(self, token=None):
        encoded_user_id = urlsafe_base64_encode(force_bytes(self.user.pk))
        reset_token = token or default_token_generator.make_token(self.user)
        return reverse(
            'accounts:reset_password',
            kwargs={'uidb64': encoded_user_id, 'token': reset_token},
        )

    def test_valid_password_reset_changes_hash_and_token_cannot_be_reused(self):
        refresh = RefreshToken.for_user(self.user)
        token = default_token_generator.make_token(self.user)
        response = self.client.post(
            self._reset_url(token),
            {
                'new_password': 'Another-Valid-Password-456!',
                'confirm_password': 'Another-Valid-Password-456!',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Another-Valid-Password-456!'))
        self.assertNotIn('password', response.data)
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=str(refresh['jti'])).exists())
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}'
        )
        self.assertEqual(self.client.get(self.me_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.credentials()
        reused = self.client.post(
            self._reset_url(token),
            {
                'new_password': 'Third-Valid-Password-789!',
                'confirm_password': 'Third-Valid-Password-789!',
            },
            format='json',
        )
        self.assertEqual(reused.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_rejects_invalid_expired_and_weak_password_requests(self):
        invalid = self.client.post(
            self._reset_url('invalid-token'),
            {
                'new_password': 'Another-Valid-Password-456!',
                'confirm_password': 'Another-Valid-Password-456!',
            },
            format='json',
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

        with override_settings(PASSWORD_RESET_TIMEOUT=30):
            with patch.object(
                default_token_generator,
                '_now',
                return_value=datetime.now() - timedelta(hours=1),
            ):
                expired_token = default_token_generator.make_token(self.user)
            expired_url = self._reset_url(expired_token)
            expired = self.client.post(
                expired_url,
                {
                    'new_password': 'Another-Valid-Password-456!',
                    'confirm_password': 'Another-Valid-Password-456!',
                },
                format='json',
            )
        self.assertEqual(expired.status_code, status.HTTP_400_BAD_REQUEST)

        weak = self.client.post(
            self._reset_url(),
            {'new_password': 'short', 'confirm_password': 'short'},
            format='json',
        )
        self.assertEqual(weak.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', weak.data)

    def test_authenticated_password_change_validates_current_password_and_revokes_refresh(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}'
        )
        bad_current = self.client.post(
            self.change_password_url,
            {
                'current_password': 'wrong-password',
                'new_password': 'Another-Valid-Password-456!',
                'confirm_password': 'Another-Valid-Password-456!',
            },
            format='json',
        )
        self.assertEqual(bad_current.status_code, status.HTTP_400_BAD_REQUEST)

        changed = self.client.post(
            self.change_password_url,
            {
                'current_password': 'Current-Password-123!',
                'new_password': 'Another-Valid-Password-456!',
                'confirm_password': 'Another-Valid-Password-456!',
            },
            format='json',
        )
        self.assertEqual(changed.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', changed.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Another-Valid-Password-456!'))
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=str(refresh['jti'])).exists())
        self.assertEqual(self.client.get(self.me_url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_change_requires_authentication_and_validates_new_password(self):
        payload = {
            'current_password': 'Current-Password-123!',
            'new_password': 'short',
            'confirm_password': 'short',
        }
        self.assertEqual(
            self.client.post(self.change_password_url, payload, format='json').status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.client.force_authenticate(self.user)
        response = self.client.post(self.change_password_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)

    def test_profile_get_and_patch_only_expose_and_update_permitted_self_fields(self):
        self.client.force_authenticate(self.user)
        current = self.client.get(self.me_url)
        self.assertEqual(current.status_code, status.HTTP_200_OK)
        self.assertEqual(current.data['phone_number'], '08012345678')
        self.assertEqual(current.data['role'], CustomUser.Role.STUDENT)
        self.assertNotIn('password', current.data)

        updated = self.client.patch(
            self.me_url,
            {'first_name': 'Updated', 'phone_number': '08099999999'},
            format='json',
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.student.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.phone_number, '08099999999')
        self.assertEqual(self.student.matric_number, 'MSC-OWNER-1')
        self.assertEqual(self.student.status, StudentProfile.Status.ACTIVE)

    def test_profile_update_rejects_restricted_fields_and_requires_authentication(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            self.me_url,
            {
                'role': CustomUser.Role.ADMIN,
                'email': 'attacker@example.com',
                'status': StudentProfile.Status.SUSPENDED,
                'matric_number': 'ALTERED-ID',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.student.refresh_from_db()
        self.assertEqual(self.user.role, CustomUser.Role.STUDENT)
        self.assertEqual(self.user.email, 'account-owner@example.com')
        self.assertEqual(self.student.status, StudentProfile.Status.ACTIVE)
        self.assertEqual(self.student.matric_number, 'MSC-OWNER-1')

        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.me_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            self.client.patch(self.me_url, {'first_name': 'No'}, format='json').status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
