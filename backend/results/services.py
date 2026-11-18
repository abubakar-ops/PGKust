from collections import defaultdict

from courses.models import CourseAllocation, Enrollment
from .models import Result


def get_batch_progress(batch):
    """Summarize required result submissions for each allocation in a batch."""
    allocations = list(
        CourseAllocation.objects.filter(
            session=batch.session,
            semester=batch.semester,
            course__programme__programme_type=batch.programme_type,
        ).select_related("course", "course__programme", "lecturer__user")
    )
    allocation_ids = [allocation.id for allocation in allocations]
    enrollments_by_allocation = defaultdict(list)
    for enrollment in Enrollment.objects.filter(
        allocation_id__in=allocation_ids,
        status=Enrollment.Status.APPROVED,
    ).select_related("student__user").order_by("student__matric_number"):
        enrollments_by_allocation[enrollment.allocation_id].append(enrollment)

    submitted_enrollment_ids = set(
        Result.objects.filter(
            batch=batch,
            enrollment__allocation_id__in=allocation_ids,
            enrollment__status=Enrollment.Status.APPROVED,
        ).values_list("enrollment_id", flat=True)
    )
    submitted_results_by_allocation = defaultdict(list)
    for result in Result.objects.filter(
        batch=batch,
        enrollment__allocation_id__in=allocation_ids,
        enrollment__status=Enrollment.Status.APPROVED,
    ).select_related("enrollment__student__user").order_by(
        "enrollment__student__matric_number"
    ):
        submitted_results_by_allocation[result.enrollment.allocation_id].append({
            "matric_number": result.enrollment.student.matric_number,
            "student_name": result.enrollment.student.user.get_full_name(),
            "score": result.score,
            "grade": result.grade,
            "grade_point": result.grade_point,
        })

    courses = []
    for allocation in allocations:
        expected_enrollments = enrollments_by_allocation[allocation.id]
        missing_enrollments = [
            enrollment for enrollment in expected_enrollments
            if enrollment.id not in submitted_enrollment_ids
        ]
        expected_count = len(expected_enrollments)
        result_count = expected_count - len(missing_enrollments)
        if not expected_count:
            progress_status = "NO_ENROLLMENTS"
        elif result_count == 0:
            progress_status = "NOT_UPLOADED"
        elif result_count < expected_count:
            progress_status = "INCOMPLETE"
        else:
            progress_status = "COMPLETE"

        courses.append({
            "allocation": allocation.id,
            "course_code": allocation.course.code,
            "course_title": allocation.course.title,
            "programme_name": allocation.course.programme.name,
            "lecturer": allocation.lecturer.user.get_full_name(),
            "lecturer_email": allocation.lecturer.user.email,
            "status": progress_status,
            "submitted": progress_status in ("COMPLETE", "NO_ENROLLMENTS"),
            "expected_result_count": expected_count,
            "result_count": result_count,
            "missing_students": [
                {
                    "matric_number": enrollment.student.matric_number,
                    "student_name": enrollment.student.user.get_full_name(),
                }
                for enrollment in missing_enrollments
            ],
            "submitted_results": submitted_results_by_allocation[allocation.id],
        })

    return {
        "expected_course_count": len(courses),
        "submitted_course_count": sum(course["status"] == "COMPLETE" for course in courses),
        "missing_course_count": sum(
            course["status"] in ("NOT_UPLOADED", "INCOMPLETE") for course in courses
        ),
        "no_enrollment_course_count": sum(
            course["status"] == "NO_ENROLLMENTS" for course in courses
        ),
        "courses": courses,
    }
