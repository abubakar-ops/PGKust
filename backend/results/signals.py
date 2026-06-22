from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .grading import GradingEngine
from decimal import Decimal


@receiver(post_save, sender='results.Result')
def recompute_gpa_on_result_save(sender, instance, **kwargs):
    """
    After any Result is saved, recompute SemesterGPA and CumulativeGPA
    for the affected student. Results are stored but remain hidden from
    students until the SemesterResultBatch is approved by the coordinator.
    """
    from .models import SemesterGPA, CumulativeGPA, Result

    student = instance.enrollment.student
    session = instance.enrollment.allocation.session
    semester = instance.enrollment.allocation.semester

    # --- Recompute semester GPA ---
    semester_results = Result.objects.filter(
        enrollment__student=student,
        enrollment__allocation__session=session,
        enrollment__allocation__semester=semester,
    ).select_related('enrollment__allocation__course')

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

    SemesterGPA.objects.update_or_create(
        student=student, session=session, semester=semester,
        defaults={'gpa': gpa, 'total_credit_units': total_cu, 'total_quality_points': total_qp},
    )

    # --- Recompute cumulative CGPA across all semesters ---
    all_results = Result.objects.filter(
        enrollment__student=student,
    ).select_related('enrollment__allocation__course')

    all_courses_data = [
        {
            'credit_units': r.enrollment.allocation.course.credit_units,
            'grade_point': r.grade_point,
        }
        for r in all_results
    ]

    cgpa = GradingEngine.compute_cgpa(all_courses_data)
    classification = GradingEngine.classify(cgpa)
    total_all_cu = sum(c['credit_units'] for c in all_courses_data)
    total_all_qp = sum(c['credit_units'] * c['grade_point'] for c in all_courses_data)

    CumulativeGPA.objects.update_or_create(
        student=student,
        defaults={
            'cgpa': cgpa,
            'classification': classification,
            'total_credit_units_earned': total_all_cu,
            'total_quality_points': total_all_qp,
        },
    )
