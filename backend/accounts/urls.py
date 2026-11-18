from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('me/',                             views.MeView.as_view(),              name='me'),
    path('change-password/',                views.ChangePasswordView.as_view(),  name='change_password'),
    path('forgot-password/',                views.ForgotPasswordView.as_view(),  name='forgot_password'),
    path('reset-password/<str:uidb64>/<str:token>/', views.ResetPasswordView.as_view(), name='reset_password'),
    path('admin/dashboard-stats/',          views.AdminDashboardStatsView.as_view(), name='admin_dashboard_stats'),
    path('register/student/',               views.StudentRegisterView.as_view(),  name='register_student'),
    path('register/lecturer/',              views.LecturerRegisterView.as_view(), name='register_lecturer'),
    path('admin/students/',                 views.AllStudentsView.as_view(),      name='all_students'),
    path('admin/students/<int:pk>/review/', views.AdminStudentReviewView.as_view(), name='admin_student_review'),
    path('admin/students/pending/',         views.PendingStudentsView.as_view(),  name='pending_students'),
    path('admin/students/<int:pk>/',        views.AdminUpdateStudentView.as_view(), name='admin_update_student'),
    path('admin/students/<int:pk>/approve/', views.ApproveStudentView.as_view(),  name='approve_student'),
    path('admin/lecturers/',                views.AllLecturersView.as_view(),     name='all_lecturers'),
    path('admin/lecturers/pending/',        views.PendingLecturersView.as_view(), name='pending_lecturers'),
    path('admin/lecturers/<int:pk>/',       views.AdminUpdateLecturerView.as_view(), name='admin_update_lecturer'),
    path('admin/lecturers/<int:pk>/approve/', views.ApproveLecturerView.as_view(), name='approve_lecturer'),
]
