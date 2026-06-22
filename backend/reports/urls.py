from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("apr/",                       views.APRListView.as_view(),               name="apr_list"),
    path("apr/create/",                views.APRCreateView.as_view(),             name="apr_create"),
    path("apr/<int:pk>/",              views.APRDetailView.as_view(),             name="apr_detail"),
    path("apr/<int:pk>/submit/",       views.APRSubmitView.as_view(),             name="apr_submit"),
    path("apr/<int:pk>/endorse/",      views.APRSupervisorEndorseView.as_view(),  name="apr_endorse"),
    path("apr/<int:pk>/approve/",      views.APRCoordinatorApproveView.as_view(), name="apr_approve"),
    path("transcript/",                views.TranscriptView.as_view(),            name="transcript"),
]
