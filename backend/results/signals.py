from django.db.models.signals import post_save
from django.dispatch import receiver
from .grading import GradingEngine


def recompute_gpa(student, session, semester):
    """
    Recompute SemesterGPA and CumulativeGPA for one student.
    Only results in APPROVED batches count — unapproved uploads must not
    leak into the GPA a student can see.
    """
    from .models import SemesterGPA, CumulativeGPA, Result, SemesterResultBatch

    approved = Result.objects.filter(
        enrollment__student=student,
        batch__status=SemesterResultBatch.Status.APPROVED,
    ).select_related('enrollment__allocation__course')

    # --- Semester GPA ---
    semester_results = [
        r for r in approved
        if r.enrollment.allocation.session_id == session.id
        and r.enrollment.allocation.semester == semester
    ]
    courses_data = [
        {
            'credit_units': r.enrollment.allocation.course.credit_units,
            'grade_point': r.grade_point,
        }
        for r in semester_results
    ]
    gpa = GradingEngine.compute_gpa(courses_data)
    total_cu = sum(c['credit_units'] for c in courses_data)
    total_qp = sum(c['credit_units'] * c['grade_point'] for c in courses_data)

    if courses_data:
        SemesterGPA.objects.update_or_create(
            student=student, session=session, semester=semester,
            defaults={'gpa': gpa, 'total_credit_units': total_cu, 'total_quality_points': total_qp},
        )
    else:
        # nothing approved for this semester — remove any stale GPA row
        SemesterGPA.objects.filter(student=student, session=session, semester=semester).delete()

    # --- Cumulative CGPA across all approved semesters ---
    all_courses_data = [
        {
            'credit_units': r.enrollment.allocation.course.credit_units,
            'grade_point': r.grade_point,
        }
        for r in approved
    ]
    cgpa = GradingEngine.compute_cgpa(all_courses_data)
    classification = GradingEngine.classify(cgpa)
    total_all_cu = sum(c['credit_units'] for c in all_courses_data)
    total_all_qp = sum(c['credit_units'] * c['grade_point'] for c in all_courses_data)

    if all_courses_data:
        CumulativeGPA.objects.update_or_create(
            student=student,
            defaults={
                'cgpa': cgpa,
                'classification': classification,
                'total_credit_units_earned': total_all_cu,
                'total_quality_points': total_all_qp,
            },
        )
    else:
        CumulativeGPA.objects.filter(student=student).delete()


def recompute_gpa_for_batch(batch):
    """Recompute GPAs for every student with a result in the given batch."""
    from .models import Result

    results = Result.objects.filter(batch=batch).select_related(
        'enrollment__student', 'enrollment__allocation__session'
    )
    seen = set()
    for r in results:
        student = r.enrollment.student
        session = r.enrollment.allocation.session
        semester = r.enrollment.allocation.semester
        key = (student.id, session.id, semester)
        if key in seen:
            continue
        seen.add(key)
        recompute_gpa(student, session, semester)


@receiver(post_save, sender='results.Result')
def recompute_gpa_on_result_save(sender, instance, **kwargs):
    """
    After any Result is saved, recompute GPAs for the affected student.
    Because only APPROVED-batch results are counted, saving a result into a
    pending batch does not change what the student sees.
    """
    recompute_gpa(
        instance.enrollment.student,
        instance.enrollment.allocation.session,
        instance.enrollment.allocation.semester,
    )
