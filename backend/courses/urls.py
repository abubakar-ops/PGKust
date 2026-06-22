from django.urls import path
from . import views

app_name = "courses"

urlpatterns = [
    path("session/current/",                 views.CurrentSessionView.as_view(),          name="current_session"),
    path("list/",                            views.CourseListView.as_view(),               name="course_list"),
    path("timetable/",                       views.TimetableView.as_view(),                name="timetable"),
    path("enroll/",                          views.EnrollView.as_view(),                   name="enroll"),
    path("enrollments/",                     views.StudentEnrollmentListView.as_view(),    name="enrollment_list"),
    path("allocations/",                     views.LecturerAllocationListView.as_view(),  name="allocation_list"),
    path("materials/<int:allocation_pk>/",   views.MaterialListView.as_view(),             name="material_list"),
    path("materials/<int:allocation_pk>/upload/", views.MaterialUploadView.as_view(),      name="material_upload"),
    # Admin
    path("admin/allocate/",                       views.AdminAllocateCourseView.as_view(),       name="admin_allocate"),
    path("admin/timetable/",                      views.AdminTimetableCreateView.as_view(),       name="admin_timetable"),
    path("admin/enrollments/pending/",            views.AdminEnrollmentListView.as_view(),        name="admin_enrollment_list"),
    path("admin/enrollments/<int:pk>/approve/",   views.AdminApproveEnrollmentView.as_view(),     name="admin_approve_enrollment"),
]
