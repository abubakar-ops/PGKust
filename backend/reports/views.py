from django.utils import timezone
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdmin, IsActiveStudent, IsActiveLecturer, IsPGCoordinator
from courses.models import AcademicSession
from notifications.utils import notify
from .models import AnnualProgressReport
from .serializers import APRSerializer


class APRListView(APIView):
    """GET: student sees own APRs; admin sees all or filtered."""

    def get(self, request):
        if request.user.is_student:
            qs = AnnualProgressReport.objects.filter(
                student=request.user.student_profile
            ).select_related("session")
        elif request.user.is_admin_user:
            qs = AnnualProgressReport.objects.all().select_related("student__user", "session")
            status_filter = request.query_params.get("status")
            if status_filter:
                qs = qs.filter(status=status_filter)
        elif not hasattr(request.user, "lecturer_profile"):
            qs = AnnualProgressReport.objects.none()
        else:
            # Supervisor sees supervised students
            qs = AnnualProgressReport.objects.filter(
                student__supervisor=request.user.lecturer_profile
            ).select_related("student__user", "session")
        return Response(APRSerializer(qs, many=True).data)


class APRCreateView(APIView):
    """POST /api/reports/apr/  — PhD student creates a draft APR."""
    permission_classes = [IsActiveStudent]

    def post(self, request):
        profile = request.user.student_profile
        if not profile.is_phd:
            return Response({"detail": "Only PhD students can submit APRs."}, status=403)

        current = AcademicSession.current()
        if current is None:
            return Response({"detail": "No active academic session."}, status=400)
        # The APR for a session gates registration in the next one, so a student who
        # missed filing before the session rolled over may still file for the
        # immediately previous session (pass "session": <id>). Defaults to current.
        previous = AcademicSession.objects.filter(
            start_date__lt=current.start_date).order_by("-start_date").first()
        allowed = {current.pk: current}
        if previous:
            allowed[previous.pk] = previous
        try:
            session = allowed[int(request.data.get("session") or current.pk)]
        except (KeyError, ValueError, TypeError):
            return Response({"detail": "APRs can only be filed for the current or previous session."},
                            status=400)

        if AnnualProgressReport.objects.filter(student=profile, session=session).exists():
            return Response({"detail": "APR already exists for this session."}, status=400)

        fields, error = _clean_apr_fields(request.data)
        if error:
            return error
        fields.setdefault("year_of_study", 1)
        apr = AnnualProgressReport.objects.create(
            student=profile, session=session, status=AnnualProgressReport.Status.DRAFT, **fields,
        )
        return Response(APRSerializer(apr).data, status=201)


EDITABLE_STATUSES = (AnnualProgressReport.Status.DRAFT, AnnualProgressReport.Status.REJECTED)
REQUIRED_APR_FIELDS = ("research_progress", "training_activities", "next_year_plan")
APR_TEXT_FIELDS = ("research_progress", "training_activities", "publications",
                   "issues_concerns", "next_year_plan")


def _clean_apr_fields(data):
    """Pick the student-editable APR fields out of request data; (fields, error Response)."""
    fields = {}
    if "year_of_study" in data:
        try:
            year = int(data["year_of_study"])
        except (TypeError, ValueError):
            year = 0
        if not 1 <= year <= 10:
            return None, Response({"detail": "year_of_study must be a number between 1 and 10."}, status=400)
        fields["year_of_study"] = year
    for f in APR_TEXT_FIELDS:
        if f in data:
            fields[f] = "" if data[f] is None else str(data[f])
    return fields, None


class APRDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsActiveStudent()]
        return super().get_permissions()

    def get(self, request, pk):
        try:
            apr = AnnualProgressReport.objects.select_related(
                "student__user", "session", "student__supervisor__user"
            ).get(pk=pk)
        except AnnualProgressReport.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        # Access control
        if request.user.is_student and apr.student != request.user.student_profile:
            return Response({"detail": "Forbidden."}, status=403)
        if request.user.is_lecturer:
            if apr.student.supervisor != request.user.lecturer_profile:
                return Response({"detail": "Forbidden."}, status=403)
        return Response(APRSerializer(apr).data)

    def patch(self, request, pk):
        """Student updates draft APR fields."""
        try:
            apr = AnnualProgressReport.objects.get(pk=pk, student=request.user.student_profile)
        except AnnualProgressReport.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        if apr.status not in EDITABLE_STATUSES:
            return Response({"detail": "Only DRAFT or REJECTED APRs can be edited."}, status=400)
        fields, error = _clean_apr_fields(request.data)
        if error:
            return error
        for field, value in fields.items():
            setattr(apr, field, value)
        # Editing a rejected APR reopens it as a draft for resubmission.
        apr.status = AnnualProgressReport.Status.DRAFT
        apr.save()
        return Response(APRSerializer(apr).data)


class APRSubmitView(APIView):
    """POST /api/reports/apr/<pk>/submit/  — student submits to supervisor."""
    permission_classes = [IsActiveStudent]

    def post(self, request, pk):
        try:
            apr = AnnualProgressReport.objects.select_related(
                "student__supervisor__user"
            ).get(pk=pk, student=request.user.student_profile)
        except AnnualProgressReport.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        if apr.status not in EDITABLE_STATUSES:
            return Response({"detail": "APR must be in DRAFT or REJECTED to submit."}, status=400)
        if apr.student.supervisor is None:
            return Response(
                {"detail": "You have no supervisor assigned yet. Ask the PG Coordinator to assign one "
                           "before submitting."},
                status=400,
            )
        missing = [f for f in REQUIRED_APR_FIELDS if not str(getattr(apr, f) or "").strip()]
        if missing:
            return Response({"detail": "Complete all required sections before submitting.",
                             "missing": missing}, status=400)

        apr.status = AnnualProgressReport.Status.SUBMITTED
        apr.submitted_at = timezone.now()
        apr.save()

        notify(
            apr.student.supervisor.user,
            "APR Awaiting Endorsement",
            f"{request.user.get_full_name()} has submitted their APR for your endorsement.",
            "APR",
        )
        return Response({"detail": "APR submitted to supervisor."})


class APRSupervisorEndorseView(APIView):
    """POST /api/reports/apr/<pk>/endorse/  — supervisor endorses."""
    permission_classes = [IsActiveLecturer]

    def post(self, request, pk):
        try:
            apr = AnnualProgressReport.objects.select_related(
                "student__user", "student__supervisor"
            ).get(pk=pk, student__supervisor=request.user.lecturer_profile)
        except AnnualProgressReport.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        if apr.status != AnnualProgressReport.Status.SUBMITTED:
            return Response({"detail": "APR must be SUBMITTED to endorse."}, status=400)

        apr.status = AnnualProgressReport.Status.SUPERVISOR_ENDORSED
        apr.supervisor_comments = request.data.get("comments", "")
        apr.supervisor_endorsed_at = timezone.now()
        apr.save()

        # Notify PG Coordinators
        from accounts.models import AdminProfile
        for admin in AdminProfile.objects.filter(admin_role="PG_COORDINATOR"):
            notify(
                admin.user,
                "APR Endorsed — Awaiting Approval",
                f"APR for {apr.student.user.get_full_name()} has been endorsed by supervisor.",
                "APR",
            )
        return Response({"detail": "APR endorsed."})


class APRCoordinatorApproveView(APIView):
    """POST /api/reports/apr/<pk>/approve/  — PG Coordinator approves."""
    permission_classes = [IsPGCoordinator]

    def post(self, request, pk):
        try:
            apr = AnnualProgressReport.objects.select_related(
                "student__user", "student__supervisor__user"
            ).get(pk=pk)
        except AnnualProgressReport.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        if apr.status != AnnualProgressReport.Status.SUPERVISOR_ENDORSED:
            return Response({"detail": "APR must be SUPERVISOR_ENDORSED."}, status=400)

        action = request.data.get("action")
        if action == "approve":
            apr.status = AnnualProgressReport.Status.COORDINATOR_APPROVED
            apr.coordinator_comments = request.data.get("comments", "")
            apr.coordinator_approved_at = timezone.now()
            apr.coordinator = request.user.admin_profile
            apr.progression_cleared = True
            apr.save()
            notify(apr.student.user, "APR Approved",
                   "Your Annual Progress Report has been approved. You may register for next semester.",
                   "APR")
            if apr.student.supervisor:
                notify(apr.student.supervisor.user, "APR Approved",
                       f"APR for {apr.student.user.get_full_name()} has been approved.",
                       "APR")
            return Response({"detail": "APR approved. Student cleared for next semester."})
        elif action == "reject":
            apr.status = AnnualProgressReport.Status.REJECTED
            apr.coordinator_comments = request.data.get("comments", "")
            apr.save()
            notify(apr.student.user, "APR Not Approved",
                   f"Your APR was not approved: {apr.coordinator_comments}", "APR")
            return Response({"detail": "APR rejected."})
        return Response({"detail": "Invalid action."}, status=400)


class TranscriptView(APIView):
    """GET /api/reports/transcript/  — student downloads their transcript as PDF."""
    permission_classes = [IsActiveStudent]

    def get(self, request):
        try:
            from weasyprint import HTML
        except (ImportError, OSError):
            # OSError: WeasyPrint is installed but its native libraries (Pango/GTK) are missing
            return Response({"detail": "PDF generation unavailable."}, status=503)

        from results.models import SemesterResultBatch, SemesterGPA, CumulativeGPA, Result
        from django.template.loader import render_to_string

        profile = request.user.student_profile
        results = Result.objects.filter(
            enrollment__student=profile,
            batch__status=SemesterResultBatch.Status.APPROVED,
        ).select_related("enrollment__allocation__course", "batch__session").order_by(
            "batch__session__start_date", "batch__semester", "enrollment__allocation__course__code")
        gpas = {
            (g.session_id, g.semester): g
            for g in SemesterGPA.objects.filter(student=profile)
        }

        # Group into one block per (session, semester), in chronological order
        semesters = []
        for r in results:
            key = (r.batch.session_id, r.batch.semester)
            if not semesters or semesters[-1]["key"] != key:
                semesters.append({
                    "key": key,
                    "session": r.batch.session.name,
                    "semester": r.batch.get_semester_display(),
                    "results": [],
                    "gpa": gpas.get(key),
                })
            semesters[-1]["results"].append(r)

        try:
            cgpa = CumulativeGPA.objects.get(student=profile)
        except CumulativeGPA.DoesNotExist:
            cgpa = None

        html_string = render_to_string("reports/transcript.html", {
            "student": profile,
            "semesters": semesters,
            "cgpa": cgpa,
            "generated_at": timezone.localtime(),
        })
        try:
            pdf = HTML(string=html_string).write_pdf()
        except OSError:
            return Response({"detail": "PDF generation unavailable."}, status=503)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="transcript_{profile.matric_number}.pdf"'
        return response
