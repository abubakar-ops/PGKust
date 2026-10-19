from .models import FeePayment


def has_paid_fee(student, session):
    """True if the student's department fee for the given AcademicSession is approved."""
    return FeePayment.objects.filter(
        student=student, academic_year=session.name, status=FeePayment.Status.APPROVED,
    ).exists()
