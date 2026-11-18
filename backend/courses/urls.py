from django.urls import path
from . import views

app_name = "courses"

urlpatterns = [
    path("session/current/",                 views.CurrentSessionView.as_view(),          name="current_session"),
    path("list/",                            views.CourseListView.as_view(),               name="course_list"),
    path("timetable/",                       views.TimetableView.as_view(),                name="timetable"),
    path("enroll/",                          views.EnrollView.as_view(),                   name="enroll"),
    path("enrollments/",                     views.StudentEnrollmentListView.as_view(),    name="enrollment_list"),
    path("available/",                       views.AvailableAllocationsView.as_view(),     name="available_allocations"),
    path("allocations/",                     views.LecturerAllocationListView.as_view(),  name="allocation_list"),
    path("materials/recent/",                views.StudentRecentMaterialsView.as_view(),   name="material_recent"),
    path("materials/<int:allocation_pk>/",   views.MaterialListView.as_view(),             name="material_list"),
    path("materials/<int:allocation_pk>/upload/", views.MaterialUploadView.as_view(),      name="material_upload"),
    path("materials/<int:allocation_pk>/<int:material_pk>/", views.MaterialDeleteView.as_view(), name="material_delete"),
    # Admin
    path("admin/sessions/",                    views.AdminAcademicSessionListCreateView.as_view(), name="admin_session_list"),
    path("admin/sessions/<int:pk>/",           views.AdminAcademicSessionDetailView.as_view(),     name="admin_session_detail"),
    path("admin/programmes/",                  views.AdminProgrammeListCreateView.as_view(),      name="admin_programme_list"),
    path("admin/programmes/<int:pk>/",         views.AdminProgrammeDetailView.as_view(),          name="admin_programme_detail"),
    path("admin/courses/",                     views.AdminCourseListCreateView.as_view(),        name="admin_course_list"),
    path("admin/courses/<int:pk>/",            views.AdminCourseDetailView.as_view(),            name="admin_course_detail"),
    path("admin/allocate/",                       views.AdminAllocateCourseView.as_view(),       name="admin_allocate"),
    path("admin/allocations/",                    views.AdminAllocationListView.as_view(),       name="admin_allocation_list"),
    path("admin/timetable/",                      views.AdminTimetableCreateView.as_view(),       name="admin_timetable"),
    path("admin/timetable/<int:pk>/",             views.AdminTimetableDetailView.as_view(),       name="admin_timetable_detail"),
    path("admin/enrollments/pending/",            views.AdminEnrollmentListView.as_view(),        name="admin_enrollment_list"),
    path("admin/enrollments/<int:pk>/approve/",   views.AdminApproveEnrollmentView.as_view(),     name="admin_approve_enrollment"),
]
