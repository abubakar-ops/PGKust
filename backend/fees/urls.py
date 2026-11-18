from django.urls import path
from . import views

app_name = "fees"

urlpatterns = [
    path("status/",                    views.FeeStatusView.as_view(),               name="fee_status"),
    path("pay/manual/",                views.ManualPaymentView.as_view(),            name="pay_manual"),
    path("pay/online/initialize/",     views.InitiateOnlinePaymentView.as_view(),   name="pay_online_init"),
    path("webhook/paystack/",          views.PaystackWebhookView.as_view(),          name="paystack_webhook"),
    path("admin/list/",                views.AdminFeeListView.as_view(),             name="admin_fee_list"),
    path("admin/<int:pk>/approve/",    views.AdminApproveFeeView.as_view(),          name="admin_approve_fee"),
]
