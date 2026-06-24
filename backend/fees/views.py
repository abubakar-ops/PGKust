import hashlib
import hmac
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

from accounts.permissions import IsAdmin, IsActiveStudent
from notifications.utils import notify
from .models import FeePayment
from .serializers import FeePaymentSerializer


def _current_academic_year():
    from datetime import date
    y = date.today().year
    # Academic year starts September
    if date.today().month >= 9:
        return f"{y}/{y+1}"
    return f"{y-1}/{y}"


class FeeStatusView(APIView):
    """GET /api/fees/status/  — student checks their fee status for current year."""
    permission_classes = [IsActiveStudent]

    def get(self, request):
        year = _current_academic_year()
        try:
            fee = FeePayment.objects.get(
                student=request.user.student_profile, academic_year=year
            )
            return Response(FeePaymentSerializer(fee).data)
        except FeePayment.DoesNotExist:
            return Response({"academic_year": year, "status": "NOT_PAID"})


class ManualPaymentView(APIView):
    """POST /api/fees/pay/manual/  — student uploads receipt."""
    permission_classes = [IsActiveStudent]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        year = _current_academic_year()
        if FeePayment.objects.filter(
            student=request.user.student_profile,
            academic_year=year,
            status__in=[FeePayment.Status.APPROVED, FeePayment.Status.PENDING],
        ).exists():
            return Response(
                {"detail": "A payment record already exists for this year."},
                status=400
            )

        receipt = request.FILES.get("receipt")
        if not receipt:
            return Response({"detail": "Receipt file is required."}, status=400)

        fee = FeePayment.objects.create(
            student=request.user.student_profile,
            academic_year=year,
            amount=request.data.get("amount", 0),
            payment_method=FeePayment.PaymentMethod.MANUAL,
            receipt_file=receipt,
            status=FeePayment.Status.PENDING,
        )
        return Response(FeePaymentSerializer(fee).data, status=201)


class InitiateOnlinePaymentView(APIView):
    """POST /api/fees/pay/online/initialize/  — returns Paystack authorization URL."""
    permission_classes = [IsActiveStudent]

    def post(self, request):
        import requests as http_req
        year = _current_academic_year()
        if FeePayment.objects.filter(
            student=request.user.student_profile,
            academic_year=year,
            status=FeePayment.Status.APPROVED,
        ).exists():
            return Response({"detail": "Fee already paid for this year."}, status=400)

        amount_kobo = int(request.data.get("amount", 50000)) * 100
        payload = {
            "email": request.user.email,
            "amount": amount_kobo,
            "metadata": {
                "student_id": request.user.student_profile.id,
                "academic_year": year,
            },
        }
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
        resp = http_req.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers=headers,
            timeout=15,
        )
        data = resp.json()
        if not data.get("status"):
            return Response({"detail": "Paystack initialization failed."}, status=502)
        # Store a pending record
        FeePayment.objects.update_or_create(
            student=request.user.student_profile,
            academic_year=year,
            defaults={
                "payment_method": FeePayment.PaymentMethod.ONLINE,
                "status": FeePayment.Status.PENDING,
                "transaction_reference": data["data"]["reference"],
                "amount": request.data.get("amount", 50000),
            }
        )
        return Response({
            "authorization_url": data["data"]["authorization_url"],
            "reference": data["data"]["reference"],
        })


@method_decorator(csrf_exempt, name="dispatch")
class PaystackWebhookView(APIView):
    """POST /api/fees/webhook/paystack/  — Paystack server-to-server webhook."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        signature = request.headers.get("X-Paystack-Signature", "")
        body = request.body
        expected = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode(), body, hashlib.sha512
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return Response(status=400)

        payload = request.data
        if payload.get("event") != "charge.success":
            return Response(status=200)

        ref = payload["data"]["reference"]
        try:
            fee = FeePayment.objects.get(transaction_reference=ref)
        except FeePayment.DoesNotExist:
            return Response(status=200)

        fee.status = FeePayment.Status.APPROVED
        fee.approved_at = timezone.now()
        fee.save()
        notify(
            fee.student.user,
            "Fee Payment Confirmed",
            f"Your {fee.academic_year} department fee payment has been confirmed.",
            "FEE",
        )
        return Response(status=200)


class AdminFeeListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = FeePayment.objects.all().select_related("student__user").order_by("-created_at")
        s = request.query_params.get("status")
        if s:
            qs = qs.filter(status=s)
        return Response(FeePaymentSerializer(qs, many=True).data)


class AdminApproveFeeView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            fee = FeePayment.objects.select_related("student__user").get(pk=pk)
        except FeePayment.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        action = request.data.get("action")
        if action == "approve":
            fee.status = FeePayment.Status.APPROVED
            fee.approved_at = timezone.now()
            fee.save()
            notify(
                fee.student.user,
                "Fee Payment Approved",
                f"Your {fee.academic_year} department fee has been approved.",
                "FEE",
            )
            return Response({"detail": "Fee approved."})
        elif action == "reject":
            fee.status = FeePayment.Status.REJECTED
            fee.rejection_reason = request.data.get("reason", "")
            fee.save()
            notify(
                fee.student.user,
                "Fee Payment Rejected",
                f"Your fee payment for {fee.academic_year} was rejected: {fee.rejection_reason}",
                "FEE",
            )
            return Response({"detail": "Fee rejected."})
        return Response({"detail": "Invalid action."}, status=400)
