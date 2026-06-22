from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from notifications.utils import notify
from .models import CustomUser, StudentProfile, LecturerProfile, AdminProfile
from .serializers import (
    StudentRegistrationSerializer, LecturerRegistrationSerializer,
    UserMeSerializer, StudentProfileSerializer, LecturerProfileSerializer,
)
from .permissions import IsAdmin, IsStudent, IsLecturer


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/  — returns access + refresh tokens."""
    permission_classes = [AllowAny]


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
                status='PENDING',
            )
        return Response(
            {'success': True, 'detail': 'Registration submitted. Await HoD approval.'},
            status=status.HTTP_201_CREATED,
        )


class PendingStudentsView(APIView):
    """GET /api/accounts/admin/students/pending/"""
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = StudentProfile.objects.filter(status=StudentProfile.PENDING).select_related('user')
        serializer = StudentProfileSerializer(qs, many=True)
        return Response(serializer.data)


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
            profile.status = StudentProfile.ACTIVE
            profile.save()
            notify(
                recipient=profile.user,
                title='Registration Approved',
                message='Your student registration has been approved. You can now log in.',
                notification_type='REGISTRATION',
            )
            return Response({'detail': 'Student approved.'})
        elif action == 'reject':
            profile.status = StudentProfile.SUSPENDED
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


class PendingLecturersView(APIView):
    """GET /api/accounts/admin/lecturers/pending/"""
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = LecturerProfile.objects.filter(status=LecturerProfile.PENDING).select_related('user')
        serializer = LecturerProfileSerializer(qs, many=True)
        return Response(serializer.data)


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
            profile.status = LecturerProfile.ACTIVE
            profile.save()
            notify(
                recipient=profile.user,
                title='Lecturer Account Approved',
                message='Your lecturer account has been approved.',
                notification_type='REGISTRATION',
            )
            return Response({'detail': 'Lecturer approved.'})
        elif action == 'reject':
            profile.status = LecturerProfile.PENDING  # stays pending; admin can note separately
            return Response({'detail': 'Lecturer approval withheld.'})
        return Response({'detail': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)
