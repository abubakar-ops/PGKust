from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """email is the login identifier; username is auto-derived since
    AbstractUser still requires it to be unique and non-null."""
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', _('Student')
        LECTURER = 'LECTURER', _('Lecturer')
        ADMIN = 'ADMIN', _('Admin')

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return f'{self.get_full_name()} ({self.email})'

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_lecturer(self):
        return self.role == self.Role.LECTURER

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN


class StudentProfile(models.Model):
    class Programme(models.TextChoices):
        MSC = 'MSC', _('Master of Science (MSc)')
        PHD = 'PHD', _('Doctor of Philosophy (PhD)')

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending Approval')
        ACTIVE = 'ACTIVE', _('Active')
        SUSPENDED = 'SUSPENDED', _('Suspended')
        GRADUATED = 'GRADUATED', _('Graduated')

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    programme = models.CharField(max_length=3, choices=Programme.choices)
    matric_number = models.CharField(max_length=20, unique=True)
    admission_year = models.PositiveIntegerField()
    supervisor = models.ForeignKey(
        'LecturerProfile', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='supervised_students', help_text='Required for PhD students')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    registration_note = models.TextField(blank=True, help_text='Admin notes or rejection reason')

    class Meta:
        verbose_name = _('Student Profile')
        verbose_name_plural = _('Student Profiles')

    def __str__(self):
        return f'{self.matric_number} - {self.user.get_full_name()} ({self.programme})'

    @property
    def is_msc(self):
        return self.programme == self.Programme.MSC

    @property
    def is_phd(self):
        return self.programme == self.Programme.PHD

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE


class LecturerProfile(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending Approval')
        ACTIVE = 'ACTIVE', _('Active')

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='lecturer_profile')
    staff_id = models.CharField(max_length=20, unique=True)
    specialization = models.CharField(max_length=100, blank=True)
    is_supervisor = models.BooleanField(default=False, help_text='Can supervise PhD students?')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    class Meta:
        verbose_name = _('Lecturer Profile')
        verbose_name_plural = _('Lecturer Profiles')

    def __str__(self):
        return f'{self.staff_id} - {self.user.get_full_name()}'

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE


class AdminProfile(models.Model):
    class AdminRole(models.TextChoices):
        PG_COORDINATOR = 'PG_COORDINATOR', _('PG Coordinator')
        HOD = 'HOD', _('Head of Department')

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='admin_profile')
    admin_role = models.CharField(max_length=20, choices=AdminRole.choices, default=AdminRole.PG_COORDINATOR)

    class Meta:
        verbose_name = _('Admin Profile')
        verbose_name_plural = _('Admin Profiles')

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.get_admin_role_display()})'

    @property
    def is_pg_coordinator(self):
        return self.admin_role == self.AdminRole.PG_COORDINATOR

    @property
    def is_hod(self):
        return self.admin_role == self.AdminRole.HOD
