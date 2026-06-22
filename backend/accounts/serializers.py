from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import CustomUser, StudentProfile, LecturerProfile, AdminProfile


class StudentRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    matric_number = serializers.CharField(max_length=20)
    programme = serializers.ChoiceField(choices=StudentProfile.Programme.choices)
    admission_year = serializers.IntegerField()

    def validate_email(self, value):
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate_matric_number(self, value):
        if StudentProfile.objects.filter(matric_number__iexact=value).exists():
            raise serializers.ValidationError('This matric number is already registered.')
        return value.upper()

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        try:
            validate_password(data['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return data


class LecturerRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    staff_id = serializers.CharField(max_length=20)
    specialization = serializers.CharField(max_length=200, required=False, allow_blank=True)
    is_supervisor = serializers.BooleanField(default=False)

    def validate_email(self, value):
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate_staff_id(self, value):
        if LecturerProfile.objects.filter(staff_id__iexact=value).exists():
            raise serializers.ValidationError('This staff ID is already registered.')
        return value.upper()

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        try:
            validate_password(data['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return data


class StudentProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'email', 'full_name', 'phone_number', 'matric_number',
            'programme', 'admission_year', 'status', 'profile_picture',
        ]
        read_only_fields = ['id', 'email', 'matric_number', 'status']

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class LecturerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = LecturerProfile
        fields = ['id', 'email', 'full_name', 'staff_id', 'specialization', 'is_supervisor', 'status']
        read_only_fields = ['id', 'email', 'staff_id', 'status']

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class AdminProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = AdminProfile
        fields = ['id', 'email', 'full_name', 'admin_role']
        read_only_fields = ['id', 'email', 'admin_role']

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class UserMeSerializer(serializers.ModelSerializer):
    """Minimal serializer for /api/auth/me/ — returns role + profile snapshot."""
    profile = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'profile']

    def get_profile(self, obj):
        if obj.is_student:
            try:
                return StudentProfileSerializer(obj.student_profile).data
            except StudentProfile.DoesNotExist:
                return None
        if obj.is_lecturer:
            try:
                return LecturerProfileSerializer(obj.lecturer_profile).data
            except LecturerProfile.DoesNotExist:
                return None
        if obj.is_admin_user:
            try:
                return AdminProfileSerializer(obj.admin_profile).data
            except AdminProfile.DoesNotExist:
                return None
        return None
