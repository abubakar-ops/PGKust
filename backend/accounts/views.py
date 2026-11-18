from django.db import transaction
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
import logging
from urllib.parse import urlsplit
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from notifications.utils import notify
from courses.models import Course, Enrollment
from .models import CustomUser, StudentProfile, LecturerProfile, AdminProfile
from .serializers import (
    StudentRegistrationSerializer, LecturerRegistrationSerializer,
    UserMeSerializer, StudentProfileSerializer, LecturerProfileSerializer,
    AdminStudentReviewSerializer,
    AdminUpdateStudentSerializer, AdminUpdateLecturerSerializer,
    PGMSTokenObtainPairSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    ChangePasswordSerializer, SelfProfileUpdateSerializer,
)
from .permissions import IsAdmin, IsStudent, IsLecturer

logger = logging.getLogger(__name__)
PASSWORD_RESET_RESPONSE = {
    'detail': (
        'If an active account matches that email and email delivery is configured, '
        'a password reset link will be sent.'
    )
}


def _invalidate_user_refresh_tokens(user):
    for token in OutstandingToken.objects.filter(user=user).iterator():
        BlacklistedToken.objects.get_or_create(token=token)


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
    """GET/PATCH the authenticated user's own account and profile snapshot."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = SelfProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(UserMeSerializer(request.user).data)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        try:
            user = CustomUser.objects.get(email__iexact=email, is_active=True)
        except CustomUser.DoesNotExist:
            user = None

        if user is not None and user.has_usable_password():
            frontend_url = settings.PASSWORD_RESET_FRONTEND_URL.rstrip('/')
            parsed_frontend_url = urlsplit(frontend_url)
            unsafe_production_mail = not settings.DEBUG and (
                parsed_frontend_url.scheme != 'https'
                or not parsed_frontend_url.hostname
                or settings.EMAIL_BACKEND
                == 'django.core.mail.backends.console.EmailBackend'
            )
            if unsafe_production_mail:
                logger.error(
                    'Password reset email is disabled: configure an HTTPS '
                    'PASSWORD_RESET_FRONTEND_URL and a real email backend.'
                )
                return Response(PASSWORD_RESET_RESPONSE)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = (
                f"{frontend_url}"
                f"/reset-password/{uid}/{token}"
            )
            try:
                send_mail(
                    subject='Reset your ADUST PGMS password',
                    message=(
                        'A password reset was requested for your ADUST PGMS account.\n\n'
                        f'Use this link to choose a new password:\n{reset_url}\n\n'
                        'If you did not request this, you can ignore this email.'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                logger.exception('Password reset email delivery failed.')

        return Response(PASSWORD_RESET_RESPONSE)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, UnicodeDecodeError, CustomUser.DoesNotExist):
            return Response(
                {'detail': 'This password reset link is invalid or has expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {'detail': 'This password reset link is invalid or has expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PasswordResetConfirmSerializer(
            data=request.data, context={'user': user}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user.set_password(serializer.validated_data['new_password'])
            user.save(update_fields=['password'])
            _invalidate_user_refresh_tokens(user)
        return Response({'detail': 'Your password has been reset. Sign in with your new password.'})


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = serializer.save()
            _invalidate_user_refresh_tokens(user)
        return Response({
            'detail': 'Password changed. Please sign in again on this and other devices.'
        })

class AdminDashboardStatsView(APIView):
    """GET /api/accounts/admin/dashboard-stats/ — counts for the admin overview."""
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({
            'total_students': StudentProfile.objects.count(),
            'total_lecturers': LecturerProfile.objects.count(),
            'total_courses': Course.objects.count(),
            'total_enrollments': Enrollment.objects.count(),
            'pending_enrollments': Enrollment.objects.filter(
                status=Enrollment.Status.PENDING
            ).count(),
        })


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
    """GET all students; optional status and name/email/matric-number filters."""
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = StudentProfile.objects.select_related('user').all()
        status_param = request.query_params.get('status')
        if status_param:
            status_param = status_param.upper()
            if status_param not in StudentProfile.Status.values:
                return Response(
                    {'status': 'Invalid status.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            qs = qs.filter(status=status_param)
        search = request.query_params.get('search', '').strip()
        if search:
            search_query = Q()
            for term in search.split():
                search_query &= (
                    Q(user__first_name__icontains=term)
                    | Q(user__last_name__icontains=term)
                    | Q(user__email__icontains=term)
                    | Q(matric_number__icontains=term)
                )
            qs = qs.filter(search_query)
        serializer = StudentProfileSerializer(qs, many=True)
        return Response(serializer.data)


class AdminStudentReviewView(APIView):
    """GET the detailed profile and academic record summary for one student."""
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        try:
            profile = StudentProfile.objects.select_related(
                'user', 'supervisor__user'
            ).get(pk=pk)
        except StudentProfile.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminStudentReviewSerializer(profile).data)


class PendingStudentsView(APIView):
    """GET /api/accounts/admin/students/pending/"""
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = StudentProfile.objects.filter(status=StudentProfile.Status.PENDING).select_related('user')
        serializer = StudentProfileSerializer(qs, many=True)
        return Response(serializer.data)


class AdminUpdateStudentView(APIView):
    """PATCH /api/accounts/admin/students/<pk>/  — edit name, contact, matric no., programme, year."""
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        try:
            profile = StudentProfile.objects.select_related('user').get(pk=pk)
        except StudentProfile.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminUpdateStudentSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(StudentProfileSerializer(profile).data)


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


class AllLecturersView(APIView):
    """GET all lecturers; optional status and name/email/staff-ID filters."""
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = LecturerProfile.objects.select_related('user').all()
        status_param = request.query_params.get('status')
        if status_param:
            status_param = status_param.upper()
            if status_param not in LecturerProfile.Status.values:
                return Response(
                    {'status': 'Invalid status.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            qs = qs.filter(status=status_param)
        search = request.query_params.get('search', '').strip()
        if search:
            search_query = Q()
            for term in search.split():
                search_query &= (
                    Q(user__first_name__icontains=term)
                    | Q(user__last_name__icontains=term)
                    | Q(user__email__icontains=term)
                    | Q(staff_id__icontains=term)
                )
            qs = qs.filter(search_query)
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
