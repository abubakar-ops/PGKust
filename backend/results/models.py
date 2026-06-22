from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import StudentProfile
from courses.models import Enrollment, AcademicSession
from .grading import GradingEngine


class SemesterResultBatch(models.Model):
    """
    Groups all course results for a given semester/session under one approval unit.
    Students cannot see any results until the PG Coordinator approves this batch.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending Approval')
        APPROVED = 'APPROVED', _('Approved - Visible to Students')
        REJECTED = 'REJECTED', _('Rejected - Lecturers Must Re-upload')

    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='result_batches')
    semester = models.CharField(max_length=6, choices=[('FIRST', 'First Semester'), ('SECOND', 'Second Semester')])
    programme_type = models.CharField(max_length=3, choices=[('MSC', 'MSc'), ('PHD', 'PhD')])
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    coordinator_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_batches'
    )

    class Meta:
        unique_together = ('session', 'semester', 'programme_type')
        ordering = ['-session__start_date', 'semester']
        verbose_name = _('Semester Result Batch')

    def __str__(self):
        return f'{self.session} {self.semester} {self.programme_type} [{self.status}]'

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED


class Result(models.Model):
    """
    Stores the score and auto-computed grade for one student in one enrolled course.
    Triggered to recompute SemesterGPA and CumulativeGPA via post_save signal.
    """
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='result')
    batch = models.ForeignKey(SemesterResultBatch, on_delete=models.CASCADE, related_name='results')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2, editable=False)
    grade_point = models.PositiveSmallIntegerField(editable=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['enrollment__allocation__course__code']

    def __str__(self):
        return (f'{self.enrollment.student.matric_number} | '
                f'{self.enrollment.allocation.course.code} | '
                f'{self.score} ({self.grade})')

    def save(self, *args, **kwargs):
        self.grade = GradingEngine.get_grade(float(self.score))
        self.grade_point = GradingEngine.get_grade_point(float(self.score))
        super().save(*args, **kwargs)


class SemesterGPA(models.Model):
    """Computed GPA for one student for one semester. Recalculated on each result save."""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='semester_gpas')
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    semester = models.CharField(max_length=6, choices=[('FIRST', 'First Semester'), ('SECOND', 'Second Semester')])
    gpa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    total_credit_units = models.PositiveSmallIntegerField(default=0)
    total_quality_points = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ('student', 'session', 'semester')
        ordering = ['session', 'semester']

    def __str__(self):
        return f'{self.student.matric_number} | {self.session} {self.semester} GPA={self.gpa}'


class CumulativeGPA(models.Model):
    """Computed CGPA for a student across all approved semesters. One record per student."""
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='cumulative_gpa')
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    classification = models.CharField(max_length=15, default='N/A')
    total_credit_units_earned = models.PositiveSmallIntegerField(default=0)
    total_quality_points = models.PositiveSmallIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.student.matric_number} CGPA={self.cgpa} ({self.classification})'
