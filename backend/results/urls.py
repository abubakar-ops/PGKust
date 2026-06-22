from django.urls import path
from . import views

app_name = "results"

urlpatterns = [
    path("mine/",                         views.StudentResultsView.as_view(),     name="student_results"),
    path("gpa/",                          views.StudentGPAView.as_view(),         name="gpa"),
    path("upload/",                       views.LecturerResultUploadView.as_view(), name="result_upload"),
    path("batches/",                      views.BatchListView.as_view(),           name="batch_list"),
    path("batches/<int:pk>/approve/",     views.ApproveBatchView.as_view(),        name="approve_batch"),
]
