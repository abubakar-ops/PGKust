from django.test import TestCase
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from unittest.mock import patch

from .models import AdminProfile, CustomUser, LecturerProfile, StudentProfile
from .views import AdminUpdateStudentView, LecturerSupervisedStudentsView, StudentStatusView


class AdminAssignSupervisorTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = CustomUser.objects.create_user(
            email='admin@example.com',
            password='test-password',
            role=CustomUser.Role.ADMIN,
            first_name='PG',
            last_name='Coordinator',
        )
        AdminProfile.objects.create(user=self.admin)
        self.supervisor = self.create_lecturer(
            'supervisor@example.com', 'SUP-001', is_supervisor=True,
            status=LecturerProfile.Status.ACTIVE,
        )
        self.non_supervisor = self.create_lecturer(
            'lecturer@example.com', 'LEC-001', is_supervisor=False,
            status=LecturerProfile.Status.ACTIVE,
        )
        self.inactive_supervisor = self.create_lecturer(
            'inactive@example.com', 'SUP-002', is_supervisor=True,
            status=LecturerProfile.Status.PENDING,
        )

    def create_lecturer(self, email, staff_id, is_supervisor, status):
        user = CustomUser.objects.create_user(
            email=email,
            password='test-password',
            role=CustomUser.Role.LECTURER,
            first_name=staff_id,
            last_name='Lecturer',
        )
        return LecturerProfile.objects.create(
            user=user,
            staff_id=staff_id,
            is_supervisor=is_supervisor,
            status=status,
        )

    def create_student(self, programme):
        user = CustomUser.objects.create_user(
            email=f'{programme.lower()}@example.com',
            password='test-password',
            role=CustomUser.Role.STUDENT,
            first_name=programme,
            last_name='Student',
        )
        return StudentProfile.objects.create(
            user=user,
            programme=programme,
            matric_number=f'{programme}-001',
            admission_year=2026,
        )

    def patch_student(self, student, data):
        request = self.factory.patch(
            f'/api/accounts/admin/students/{student.pk}/', data, format='json')
        force_authenticate(request, user=self.admin)
        return AdminUpdateStudentView.as_view()(request, pk=student.pk)

    def test_active_supervisor_can_be_assigned_to_msc_and_phd_students(self):
        for programme in (StudentProfile.Programme.MSC, StudentProfile.Programme.PHD):
            with self.subTest(programme=programme):
                student = self.create_student(programme)

                with patch('accounts.views.notify') as notification:
                    response = self.patch_student(student, {'supervisor': self.supervisor.pk})

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data['supervisor'], self.supervisor.pk)
                self.assertEqual(response.data['supervisor_name'], self.supervisor.user.get_full_name())
                self.assertEqual(notification.call_count, 2)
                student.refresh_from_db()
                self.assertEqual(student.supervisor, self.supervisor)

    def test_assigned_lecturer_can_view_only_their_own_students(self):
        assigned_student = self.create_student(StudentProfile.Programme.MSC)
        assigned_student.supervisor = self.supervisor
        assigned_student.save(update_fields=['supervisor'])
        other_student = self.create_student(StudentProfile.Programme.PHD)
        other_student.supervisor = self.non_supervisor
        other_student.save(update_fields=['supervisor'])

        request = self.factory.get('/api/accounts/lecturer/students/')
        force_authenticate(request, user=self.supervisor.user)
        response = LecturerSupervisedStudentsView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([student['id'] for student in response.data], [assigned_student.pk])
        self.assertEqual(response.data[0]['supervisor_email'], self.supervisor.user.email)

    def test_student_is_notified_when_supervisor_is_removed(self):
        student = self.create_student(StudentProfile.Programme.PHD)
        student.supervisor = self.supervisor
        student.save(update_fields=['supervisor'])

        with patch('accounts.views.notify') as notification:
            response = self.patch_student(student, {'supervisor': None})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(notification.call_count, 2)
        self.assertEqual(notification.call_args_list[0].kwargs['recipient'], student.user)
        self.assertEqual(notification.call_args_list[1].kwargs['recipient'], self.supervisor.user)

    def test_only_active_lecturers_marked_as_supervisors_can_be_assigned(self):
        student = self.create_student(StudentProfile.Programme.MSC)

        for lecturer in (self.non_supervisor, self.inactive_supervisor):
            with self.subTest(lecturer=lecturer.staff_id):
                response = self.patch_student(student, {'supervisor': lecturer.pk})
                self.assertEqual(response.status_code, 400)

        student.refresh_from_db()
        self.assertIsNone(student.supervisor)

    def test_supervisor_assignment_can_be_cleared(self):
        student = self.create_student(StudentProfile.Programme.PHD)
        student.supervisor = self.supervisor
        student.save(update_fields=['supervisor'])

        response = self.patch_student(student, {'supervisor': None})

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['supervisor'])
        self.assertIsNone(response.data['supervisor_name'])
        student.refresh_from_db()
        self.assertIsNone(student.supervisor)


class StudentStatusTests(AdminAssignSupervisorTests):
    def change(self, student, action):
        request = self.factory.post(
            f'/api/accounts/admin/students/{student.pk}/status/', {'action': action}, format='json')
        force_authenticate(request, user=self.admin)
        with patch('accounts.views.notify') as notification:
            response = StudentStatusView.as_view()(request, pk=student.pk)
        return response, notification

    def test_transitions_and_notifications(self):
        student = self.create_student(StudentProfile.Programme.MSC)
        student.status = StudentProfile.Status.ACTIVE
        student.save()
        for action, expected in (
            ('suspend', StudentProfile.Status.SUSPENDED),
            ('reactivate', StudentProfile.Status.ACTIVE),
            ('graduate', StudentProfile.Status.GRADUATED),
            ('reactivate', StudentProfile.Status.ACTIVE),
        ):
            response, notification = self.change(student, action)
            self.assertEqual(response.status_code, 200)
            student.refresh_from_db()
            self.assertEqual(student.status, expected)
            notification.assert_called_once()

    def test_invalid_transitions_rejected(self):
        student = self.create_student(StudentProfile.Programme.PHD)
        for action in ('graduate', 'suspend', 'reactivate', 'bogus'):
            response, notification = self.change(student, action)
            self.assertEqual(response.status_code, 400)
            notification.assert_not_called()

    def test_inactive_students_cannot_login_or_refresh(self):
        from rest_framework.exceptions import AuthenticationFailed
        from rest_framework_simplejwt.tokens import RefreshToken
        from .serializers import PGMSTokenObtainPairSerializer, PGMSTokenRefreshSerializer
        student = self.create_student(StudentProfile.Programme.MSC)
        for st in (StudentProfile.Status.SUSPENDED, StudentProfile.Status.GRADUATED):
            student.status = st
            student.save()
            login = PGMSTokenObtainPairSerializer(
                data={'email': student.user.email, 'password': 'test-password'},
                context={'request': self.factory.post('/api/auth/login/')})
            with self.assertRaises(AuthenticationFailed):
                login.is_valid()
            refresh = PGMSTokenRefreshSerializer(
                data={'refresh': str(RefreshToken.for_user(student.user))})
            with self.assertRaises(AuthenticationFailed):
                refresh.is_valid()
        student.status = StudentProfile.Status.ACTIVE
        student.save()
        refresh = PGMSTokenRefreshSerializer(
            data={'refresh': str(RefreshToken.for_user(student.user))})
        self.assertTrue(refresh.is_valid())

    def test_approved_student_can_login_with_mixed_case_email(self):
        student = self.create_student(StudentProfile.Programme.MSC)
        student.status = StudentProfile.Status.ACTIVE
        student.save(update_fields=['status'])

        response = APIClient().post('/api/auth/login/', {
            'email': 'MSC@EXAMPLE.COM',
            'password': 'test-password',
        })

        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn('access', response.data)
