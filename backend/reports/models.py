from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import StudentProfile, LecturerProfile, AdminProfile
from courses.models import AcademicSession


class AnnualProgressReport(models.Model):
    """
    PhD Annual Progress Report (APR).
    Workflow: DRAFT -> SUBMITTED -> SUPERVISOR_ENDORSED -> COORDINATOR_APPROVED
    The progression_cleared flag gates next-semester departmental registration.
    """
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft (In Progress)')
        SUBMITTED = 'SUBMITTED', _('Submitted - Awaiting Supervisor')
        SUPERVISOR_ENDORSED = 'SUPERVISOR_ENDORSED', _('Supervisor Endorsed - Awaiting Coordinator')
        COORDINATOR_APPROVED = 'COORDINATOR_APPROVED', _('Approved - Progression Cleared')
        REJECTED = 'REJECTED', _('Rejected')

    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE,
        related_name='annual_reports',
        limit_choices_to={'programme': 'PHD'},
    )
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='apr_reports')
    year_of_study = models.PositiveSmallIntegerField(help_text='e.g. 1 for Year 1')

    # --- APR Sections ---
    research_progress = models.TextField(
        help_text='Summarise research progress, achievements and milestones reached this year.'
    )
    training_activities = models.TextField(
        help_text='List conferences attended, workshops, seminars, and skills training.'
    )
    publications = models.TextField(
        blank=True,
        help_text='List any publications, papers submitted, or conference presentations.'
    )
    issues_concerns = models.TextField(
        blank=True,
        help_text='Any challenges, concerns, or welfare issues to raise.'
    )
    next_year_plan = models.TextField(
        help_text='Objectives and planned activities for the next 12 months.'
    )

    # --- Workflow Status ---
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT)
    progression_cleared = models.BooleanField(
        default=False,
        help_text='Set to True only when Coordinator approves. Gates next-semester registration.'
    )

    # --- Supervisor endorsement ---
    supervisor_comments = models.TextField(blank=True)
    supervisor_endorsed_at = models.DateTimeField(null=True, blank=True)

    # --- Coordinator approval ---
    coordinator_comments = models.TextField(blank=True)
    coordinator_approved_at = models.DateTimeField(null=True, blank=True)
    coordinator = models.ForeignKey(
        AdminProfile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_aprs'
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'session')
        ordering = ['-session__start_date']
        verbose_name = _('Annual Progress Report')
        verbose_name_plural = _('Annual Progress Reports')

    def __str__(self):
        return f'APR | {self.student.matric_number} | {self.session} | {self.status}'

    @property
    def is_pending_supervisor(self):
        return self.status == self.Status.SUBMITTED

    @property
    def is_pending_coordinator(self):
        return self.status == self.Status.SUPERVISOR_ENDORSED

    @property
    def is_approved(self):
        return self.status == self.Status.COORDINATOR_APPROVED
