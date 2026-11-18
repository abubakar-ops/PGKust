from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from notifications.utils import notify
from .models import CustomUser, StudentProfile, LecturerProfile, AdminProfile
from .serializers import (
    StudentRegistrationSerializer, LecturerRegistrationSerializer,
    UserMeSerializer, StudentProfileSerializer, LecturerProfileSerializer,
    AdminUpdateStudentSerializer, AdminUpdateLecturerSerializer,
    PGMSTokenObtainPairSerializer, PGMSTokenRefreshSerializer, STUDENT_INACCESSIBLE_MESSAGES,
)
from .permissions import IsActiveLecturer, IsAdmin, IsStudent, IsLecturer


def _notify_admins(title, message, link=''):
    for admin in CustomUser.objects.filter(role=CustomUser.Role.ADMIN):
        notify(recipient=admin, title=title, message=message,
               notification_type='REGISTRATION', link=link)


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/  — returns access + refresh tokens.

    Rejects pending students/lecturers (see PGMSTokenObtainPairSerializer).
    """
    permission_classes = [AllowAny]
    serializer_class = PGMSTokenObtainPairSerializer


class RefreshView(TokenRefreshView):
    """POST /api/auth/refresh/ — rejects suspended/graduated students."""
    serializer_class = PGMSTokenRefreshSerializer


class LogoutView(APIView):
    """POST /api/auth/logout/  — blacklists the refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({'detail': 'Token is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)


class MeView(APIView):
    """GET /api/accounts/me/  — returns the authenticated user + profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, 'student_profile', None) if request.user.is_student else None
        if profile and profile.status != StudentProfile.Status.ACTIVE:
            return Response({'detail': STUDENT_INACCESSIBLE_MESSAGES[profile.status]},
                            status=status.HTTP_403_FORBIDDEN)
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)


class StudentRegisterView(APIView):
    """POST /api/accounts/register/student/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        with transaction.atomic():
            user = CustomUser.objects.create_user(
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone_number=data.get('phone_number', ''),
                role=CustomUser.Role.STUDENT,
            )
            StudentProfile.objects.create(
                user=user,
                matric_number=data['matric_number'],
                programme=data['programme'],
                admission_year=data['admission_year'],
                status=StudentProfile.Status.PENDING,
            )
        _notify_admins(
            title='New Student Registration',
            message=f'{user.get_full_name()} ({data["matric_number"]}) has registered and is awaiting approval.',
            link='/admin/students',
        )
        return Response(
            {'success': True, 'detail': 'Registration submitted. Await PG Coordinator approval.'},
            status=status.HTTP_201_CREATED,
        )


class LecturerRegisterView(APIView):
    """POST /api/accounts/register/lecturer/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LecturerRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        with transaction.atomic():
            user = CustomUser.objects.create_user(
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone_number=data.get('phone_number', ''),
                role=CustomUser.Role.LECTURER,
            )
            LecturerProfile.objects.create(
                user=user,
                staff_id=data['staff_id'],
                specialization=data.get('specialization', ''),
                is_supervisor=data.get('is_supervisor', False),
                status=LecturerProfile.Status.PENDING,
            )
        _notify_admins(
            title='New Lecturer Registration',
            message=f'{user.get_full_name()} ({data["staff_id"]}) has registered and is awaiting approval.',
            link='/admin/lecturers',
        )
        return Response(
            {'success': True, 'detail': 'Registration submitted. Await HoD approval.'},
            status=status.HTTP_201_CREATED,
        )


class AllStudentsView(APIView):
    """GET /api/accounts/admin/students/  — all students, optional ?status=ACTIVE filter."""
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = StudentProfile.objects.select_related('user', 'supervisor__user').all()
        status_param = request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())
        serializer = StudentProfileSerializer(qs, many=True)
        return Response(serializer.data)


class PendingStudentsView(APIView):
    """GET /api/accounts/admin/students/pending/"""
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = StudentProfile.objects.filter(status=StudentProfile.Status.PENDING).select_related(
            'user', 'supervisor__user')
        serializer = StudentProfileSerializer(qs, many=True)
        return Response(serializer.data)


class AdminUpdateStudentView(APIView):
    """PATCH /api/accounts/admin/students/<pk>/  — edit name, contact, matric no., programme, year."""
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        try:
            profile = StudentProfile.objects.select_related('user', 'supervisor__user').get(pk=pk)
        except StudentProfile.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminUpdateStudentSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        previous_supervisor = profile.supervisor
        serializer.save()
        current_supervisor = profile.supervisor
        if previous_supervisor != current_supervisor:
            student_name = profile.user.get_full_name()
            programme = profile.get_programme_display()
            if current_supervisor:
                supervisor_message = (
                    f'You have been assigned as the academic supervisor for {student_name} '
                    f'({profile.matric_number}), a {programme} student.'
                )
                notify(
                    recipient=current_supervisor.user,
                    title='New Student Assigned',
                    message=supervisor_message,
                    notification_type='SUPERVISOR',
                    link='/lecturer/dashboard',
                )
                student_message = (
                    f'{current_supervisor.user.get_full_name()} has been assigned as your academic '
                    f'supervisor. Contact: {current_supervisor.user.email}'
                )
                if current_supervisor.user.phone_number:
                    student_message += f' · {current_supervisor.user.phone_number}'
                student_title = 'Academic Supervisor Assigned'
            else:
                student_message = (
                    'Your academic supervisor assignment has been removed. '
                    'Please contact the PG Coordinator for more information.'
                )
                student_title = 'Academic Supervisor Assignment Updated'

            notify(
                recipient=profile.user,
                title=student_title,
                message=student_message,
                notification_type='SUPERVISOR',
                link='/student/dashboard',
            )
            if previous_supervisor:
                notify(
                    recipient=previous_supervisor.user,
                    title='Student Assignment Updated',
                    message=f'You are no longer assigned as the academic supervisor for '
                    f'{student_name} ({profile.matric_number}).',
                    notification_type='SUPERVISOR',
                    link='/lecturer/dashboard',
                )
        return Response(StudentProfileSerializer(profile).data)


class LecturerSupervisedStudentsView(APIView):
    """GET /api/accounts/lecturer/students/ — students assigned to the lecturer."""
    permission_classes = [IsActiveLecturer]

    def get(self, request):
        students = StudentProfile.objects.filter(
            supervisor__user=request.user,
        ).select_related('user', 'supervisor__user').order_by(
            'user__last_name', 'user__first_name', 'matric_number')
        return Response(StudentProfileSerializer(students, many=True).data)


class ApproveStudentView(APIView):
    """POST /api/accounts/admin/students/<pk>/approve/  — action: approve | reject"""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            profile = StudentProfile.objects.select_related('user').get(pk=pk)
        except StudentProfile.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')
        if action == 'approve':
            profile.status = StudentProfile.Status.ACTIVE
            profile.save()
            notify(
                recipient=profile.user,
                title='Registration Approved',
                message='Your student registration has been approved. You can now log in.',
                notification_type='REGISTRATION',
            )
            return Response({'detail': 'Student approved.'})
        elif action == 'reject':
            profile.status = StudentProfile.Status.SUSPENDED
            profile.save()
            notify(
                recipient=profile.user,
                title='Registration Rejected',
                message='Your student registration was not approved. Contact the PG Coordinator.',
                notification_type='REGISTRATION',
            )
            return Response({'detail': 'Student rejected.'})
        return Response({'detail': 'Invalid action. Use approve or reject.'},
                        status=status.HTTP_400_BAD_REQUEST)


class StudentStatusView(APIView):
    """POST /api/accounts/admin/students/<pk>/status/ — action: reactivate | graduate | suspend"""
    permission_classes = [IsAdmin]

    TRANSITIONS = {
        'reactivate': (
            {StudentProfile.Status.SUSPENDED, StudentProfile.Status.GRADUATED},
            StudentProfile.Status.ACTIVE,
            'Account Reactivated',
            'Your student account has been reactivated. You can log in again.',
        ),
        'graduate': (
            {StudentProfile.Status.ACTIVE},
            StudentProfile.Status.GRADUATED,
            'Congratulations on Graduating',
            'You have been marked as graduated. Portal access has now ended.',
        ),
        'suspend': (
            {StudentProfile.Status.ACTIVE},
            StudentProfile.Status.SUSPENDED,
            'Account Suspended',
            'Your student account has been suspended. Contact the PG Coordinator.',
        ),
    }

    def post(self, request, pk):
        try:
            profile = StudentProfile.objects.select_related('user').get(pk=pk)
        except StudentProfile.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        transition = self.TRANSITIONS.get(request.data.get('action'))
        if transition is None:
            return Response({'detail': 'Invalid action. Use reactivate, graduate or suspend.'},
                            status=status.HTTP_400_BAD_REQUEST)
        allowed_from, new_status, title, message = transition
        if profile.status not in allowed_from:
            return Response(
                {'detail': f'Cannot do this for a student whose status is {profile.status}.'},
                status=status.HTTP_400_BAD_REQUEST)

        profile.status = new_status
        profile.save(update_fields=['status'])
        notify(recipient=profile.user, title=title, message=message,
               notification_type='REGISTRATION')
        return Response(StudentProfileSerializer(profile).data)


class AllLecturersView(APIView):
    """GET /api/accounts/admin/lecturers/  — all lecturers, optional ?status=ACTIVE filter."""
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = LecturerProfile.objects.select_related('user').all()
        status_param = request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())
        serializer = LecturerProfileSerializer(qs, many=True)
        return Response(serializer.data)


class PendingLecturersView(APIView):
    """GET /api/accounts/admin/lecturers/pending/"""
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = LecturerProfile.objects.filter(status=LecturerProfile.Status.PENDING).select_related('user')
        serializer = LecturerProfileSerializer(qs, many=True)
        return Response(serializer.data)


class AdminUpdateLecturerView(APIView):
    """PATCH /api/accounts/admin/lecturers/<pk>/  — edit name, contact, staff ID, specialization."""
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        try:
            profile = LecturerProfile.objects.select_related('user').get(pk=pk)
        except LecturerProfile.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminUpdateLecturerSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(LecturerProfileSerializer(profile).data)


class ApproveLecturerView(APIView):
    """POST /api/accounts/admin/lecturers/<pk>/approve/"""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            profile = LecturerProfile.objects.select_related('user').get(pk=pk)
        except LecturerProfile.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')
        if action == 'approve':
            profile.status = LecturerProfile.Status.ACTIVE
            profile.save()
            notify(
                recipient=profile.user,
                title='Lecturer Account Approved',
                message='Your lecturer account has been approved.',
                notification_type='REGISTRATION',
            )
            return Response({'detail': 'Lecturer approved.'})
        elif action == 'reject':
            profile.status = LecturerProfile.Status.PENDING  # stays pending; admin can note separately
            return Response({'detail': 'Lecturer approval withheld.'})
        return Response({'detail': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)
