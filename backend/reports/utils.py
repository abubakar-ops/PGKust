from courses.models import AcademicSession
from .models import AnnualProgressReport


def phd_progression_cleared(student, session):
    """
    PhD students must have a coordinator-approved APR for the previous session
    before registering courses in a new one. Students in their first session
    (no earlier session since their admission year) are exempt. Always True for MSc.
    """
    if not student.is_phd:
        return True
    previous = AcademicSession.objects.filter(
        start_date__lt=session.start_date
    ).order_by('-start_date').first()
    if previous is None or previous.start_date.year < student.admission_year:
        return True
    return AnnualProgressReport.objects.filter(
        student=student, session=previous, progression_cleared=True,
    ).exists()
