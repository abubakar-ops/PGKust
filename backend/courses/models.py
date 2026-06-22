from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import StudentProfile, LecturerProfile


class AcademicSession(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text='e.g. 2024/2025')
    is_current = models.BooleanField(default=False)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicSession.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Programme(models.Model):
    class ProgrammeType(models.TextChoices):
        MSC = 'MSC', _('Master of Science (MSc)')
        PHD = 'PHD', _('Doctor of Philosophy (PhD)')

    name = models.CharField(max_length=100)
    programme_type = models.CharField(max_length=3, choices=ProgrammeType.choices)
    duration_years = models.PositiveSmallIntegerField(default=2)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('name', 'programme_type')

    def __str__(self):
        return f'{self.name} ({self.programme_type})'


class Course(models.Model):
    class Semester(models.TextChoices):
        FIRST = 'FIRST', _('First Semester')
        SECOND = 'SECOND', _('Second Semester')

    code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=150)
    credit_units = models.PositiveSmallIntegerField()
    semester = models.CharField(max_length=6, choices=Semester.choices)
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='courses')
    is_elective = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.title} ({self.credit_units} CU)'


class CourseAllocation(models.Model):
    lecturer = models.ForeignKey(LecturerProfile, on_delete=models.CASCADE, related_name='allocations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='allocations')
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='allocations')
    semester = models.CharField(max_length=6, choices=Course.Semester.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'session', 'semester')
        ordering = ['session', 'semester', 'course']

    def __str__(self):
        return f'{self.course.code} -> {self.lecturer} ({self.session}, {self.semester})'


class Timetable(models.Model):
    class Day(models.TextChoices):
        MONDAY = 'MON', _('Monday')
        TUESDAY = 'TUE', _('Tuesday')
        WEDNESDAY = 'WED', _('Wednesday')
        THURSDAY = 'THU', _('Thursday')
        FRIDAY = 'FRI', _('Friday')

    allocation = models.OneToOneField(CourseAllocation, on_delete=models.CASCADE, related_name='timetable')
    day = models.CharField(max_length=3, choices=Day.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=80)

    class Meta:
        ordering = ['day', 'start_time']

    def __str__(self):
        return f'{self.allocation.course.code} | {self.day} {self.start_time}-{self.end_time} @ {self.venue}'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('Start time must be before end time.')
        clashes = Timetable.objects.filter(
            allocation__session=self.allocation.session,
            allocation__semester=self.allocation.semester,
            day=self.day,
            venue=self.venue,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        ).exclude(pk=self.pk)
        if clashes.exists():
            raise ValidationError(f'Timetable clash: {self.venue} is already booked at this time.')


class Enrollment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending Approval')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    allocation = models.ForeignKey(CourseAllocation, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        unique_together = ('student', 'allocation')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f'{self.student.matric_number} -> {self.allocation.course.code} [{self.status}]'

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED


def material_upload_path(instance, filename):
    return f'materials/{instance.allocation.session}/{instance.allocation.course.code}/{filename}'


class CourseMaterial(models.Model):
    allocation = models.ForeignKey(CourseAllocation, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to=material_upload_path)
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.title} [{self.allocation.course.code}]'

    def get_file_extension(self):
        import os
        _, ext = os.path.splitext(self.file.name)
        return ext.lower()
