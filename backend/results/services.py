from django.db.models import Count, Q

from courses.models import CourseAllocation


def get_batch_progress(batch):
    """Return allocation-level submission progress for a shared result batch."""
    allocations = CourseAllocation.objects.filter(
        session=batch.session,
        semester=batch.semester,
        course__programme__programme_type=batch.programme_type,
    ).select_related("course", "course__programme", "lecturer__user").annotate(
        result_count=Count(
            "enrollments__result",
            filter=Q(enrollments__result__batch=batch),
            distinct=True,
        )
    )

    courses = [
        {
            "allocation": allocation.id,
            "course_code": allocation.course.code,
            "course_title": allocation.course.title,
            "lecturer": allocation.lecturer.user.get_full_name(),
            "lecturer_email": allocation.lecturer.user.email,
            "submitted": allocation.result_count > 0,
            "result_count": allocation.result_count,
        }
        for allocation in allocations
    ]
    return {
        "expected_course_count": len(courses),
        "submitted_course_count": sum(course["submitted"] for course in courses),
        "missing_course_count": sum(not course["submitted"] for course in courses),
        "courses": courses,
    }
