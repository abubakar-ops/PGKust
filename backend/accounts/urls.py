from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('me/',                             views.MeView.as_view(),              name='me'),
    path('register/student/',               views.StudentRegisterView.as_view(),  name='register_student'),
    path('register/lecturer/',              views.LecturerRegisterView.as_view(), name='register_lecturer'),
    path('admin/students/pending/',         views.PendingStudentsView.as_view(),  name='pending_students'),
    path('admin/students/<int:pk>/',        views.AdminUpdateStudentView.as_view(), name='admin_update_student'),
    path('admin/students/<int:pk>/approve/', views.ApproveStudentView.as_view(),  name='approve_student'),
    path('admin/lecturers/pending/',        views.PendingLecturersView.as_view(), name='pending_lecturers'),
    path('admin/lecturers/<int:pk>/',       views.AdminUpdateLecturerView.as_view(), name='admin_update_lecturer'),
    path('admin/lecturers/<int:pk>/approve/', views.ApproveLecturerView.as_view(), name='approve_lecturer'),
]
