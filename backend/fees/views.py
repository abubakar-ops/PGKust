import hashlib
import hmac
import logging
import os
from decimal import Decimal

import requests
from django.conf import settings
from django.http import FileResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

from accounts.permissions import IsAdmin, IsActiveStudent
from courses.models import AcademicSession
from notifications.utils import notify
from .models import FeePayment
from .serializers import FeePaymentSerializer

logger = logging.getLogger(__name__)

ALLOWED_RECEIPT_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png']
MAX_RECEIPT_SIZE_MB = 5


def _session_and_fee():
    """
    Return (session, amount_due, None) for the current AcademicSession, or
    (None, None, error Response) if there is no current session or its fee is unset.
    The amount always comes from the session, never from the client.
    """
    session = AcademicSession.current()
    if session is None:
        return None, None, Response({"detail": "No active academic session."}, status=400)
    if session.department_fee <= 0:
        return None, None, Response(
            {"detail": f"The department fee for {session.name} has not been set yet."}, status=400)
    return session, session.department_fee, None


class FeeStatusView(APIView):
    """GET /api/fees/status/  — student checks their fee status for the current session."""
    permission_classes = [IsActiveStudent]

    def get(self, request):
        session = AcademicSession.current()
        if session is None:
            return Response({"academic_year": None, "status": "NO_SESSION", "amount_due": None})
        fee = FeePayment.objects.filter(
            student=request.user.student_profile, academic_year=session.name
        ).first()
        data = FeePaymentSerializer(fee).data if fee else {
            "academic_year": session.name, "status": "NOT_PAID",
        }
        data["amount_due"] = session.department_fee
        return Response(data)


class ManualPaymentView(APIView):
    """POST /api/fees/pay/manual/  — student uploads a bank receipt (field: receipt)."""
    permission_classes = [IsActiveStudent]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        session, amount_due, error = _session_and_fee()
        if error:
            return error
        profile = request.user.student_profile
        existing = FeePayment.objects.filter(student=profile, academic_year=session.name).first()
        if existing and existing.status == FeePayment.Status.APPROVED:
            return Response({"detail": "Your fee for this session is already paid."}, status=400)
        if (existing and existing.status == FeePayment.Status.PENDING
                and existing.payment_method == FeePayment.PaymentMethod.MANUAL):
            return Response({"detail": "Your uploaded receipt is still awaiting review."}, status=400)
        # An abandoned online checkout (ONLINE + PENDING) may be replaced by a manual
        # receipt; if Paystack later confirms it, the webhook matches it by metadata.

        receipt = request.FILES.get("receipt")
        if not receipt:
            return Response({"detail": "Receipt file is required."}, status=400)
        ext = os.path.splitext(receipt.name)[1].lower()
        if ext not in ALLOWED_RECEIPT_EXTENSIONS:
            return Response({"detail": f"Receipt must be one of {', '.join(ALLOWED_RECEIPT_EXTENSIONS)}."},
                            status=400)
        if receipt.size > MAX_RECEIPT_SIZE_MB * 1024 * 1024:
            return Response({"detail": f"Receipt must be under {MAX_RECEIPT_SIZE_MB} MB."}, status=400)

        # A previously rejected payment is reused: one record per student per session.
        fee = existing or FeePayment(student=profile, academic_year=session.name)
        fee.amount = amount_due
        fee.payment_method = FeePayment.PaymentMethod.MANUAL
        fee.status = FeePayment.Status.PENDING
        fee.receipt_file = receipt
        fee.transaction_reference = None
        fee.rejection_reason = ""
        fee.approved_at = None
        fee.approved_by = None
        fee.save()
        return Response(FeePaymentSerializer(fee).data, status=201)


class InitiateOnlinePaymentView(APIView):
    """POST /api/fees/pay/online/initialize/  — returns a Paystack authorization URL."""
    permission_classes = [IsActiveStudent]

    def post(self, request):
        session, amount_due, error = _session_and_fee()
        if error:
            return error
        profile = request.user.student_profile
        existing = FeePayment.objects.filter(student=profile, academic_year=session.name).first()
        if existing and existing.status == FeePayment.Status.APPROVED:
            return Response({"detail": "Fee already paid for this session."}, status=400)
        if (existing and existing.status == FeePayment.Status.PENDING
                and existing.payment_method == FeePayment.PaymentMethod.MANUAL):
            return Response({"detail": "Your uploaded receipt is still awaiting review."}, status=400)

        payload = {
            "email": request.user.email,
            "amount": int(amount_due * 100),  # kobo
            "metadata": {"student_id": profile.id, "academic_year": session.name},
        }
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
        try:
            resp = requests.post(
                "https://api.paystack.co/transaction/initialize",
                json=payload, headers=headers, timeout=15,
            )
            data = resp.json()
        except (requests.RequestException, ValueError):
            return Response({"detail": "Could not reach Paystack. Try again later."}, status=502)
        if not data.get("status"):
            return Response({"detail": "Paystack initialization failed."}, status=502)

        FeePayment.objects.update_or_create(
            student=profile,
            academic_year=session.name,
            defaults={
                "payment_method": FeePayment.PaymentMethod.ONLINE,
                "status": FeePayment.Status.PENDING,
                "transaction_reference": data["data"]["reference"],
                "amount": amount_due,
                "receipt_file": None,
                "rejection_reason": "",
            },
        )
        return Response({
            "authorization_url": data["data"]["authorization_url"],
            "reference": data["data"]["reference"],
            "amount": amount_due,
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

        data = payload.get("data") or {}
        fee = FeePayment.objects.select_related("student__user").filter(
            transaction_reference=data.get("reference")).first()
        if fee is None:
            # The reference may have been superseded (student started checkout twice,
            # then paid the first one). Fall back to the metadata we sent Paystack.
            meta = data.get("metadata") or {}
            fee = FeePayment.objects.select_related("student__user").filter(
                student_id=meta.get("student_id"), academic_year=meta.get("academic_year"),
            ).first() if meta.get("student_id") else None
        if fee is None:
            logger.error("Paystack charge %s has no matching FeePayment (metadata=%s); "
                         "reconcile manually.", data.get("reference"), data.get("metadata"))
            return Response(status=200)
        if fee.status == FeePayment.Status.APPROVED:
            return Response(status=200)  # duplicate delivery

        paid_kobo = Decimal(str(data.get("amount") or 0))
        if data.get("currency", "NGN") != "NGN" or paid_kobo < fee.amount * 100:
            logger.warning("Paystack payment %s underpaid: got %s kobo %s, expected %s NGN",
                           fee.transaction_reference, paid_kobo, data.get("currency"), fee.amount)
            return Response(status=200)  # acknowledged, but the fee stays PENDING

        fee.status = FeePayment.Status.APPROVED
        fee.approved_at = timezone.now()
        fee.payment_method = FeePayment.PaymentMethod.ONLINE
        fee.transaction_reference = data.get("reference")
        fee.paystack_payment_id = str(data.get("id", ""))
        fee.save()
        notify(
            fee.student.user,
            "Fee Payment Confirmed",
            f"Your {fee.academic_year} department fee payment has been confirmed.",
            "FEE",
        )
        return Response(status=200)


class ReceiptDownloadView(APIView):
    """GET /api/fees/<pk>/receipt/  — the uploaded receipt, for its owner or an admin."""

    def get(self, request, pk):
        try:
            fee = FeePayment.objects.select_related("student").get(pk=pk)
        except FeePayment.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        is_owner = request.user.is_student and fee.student.user_id == request.user.id
        if not (is_owner or request.user.is_admin_user):
            return Response({"detail": "Forbidden."}, status=403)
        if not fee.receipt_file:
            return Response({"detail": "No receipt uploaded for this payment."}, status=404)
        try:
            fh = fee.receipt_file.open("rb")
        except FileNotFoundError:
            return Response({"detail": "File is missing on the server."}, status=404)
        return FileResponse(fh, as_attachment=True, filename=os.path.basename(fee.receipt_file.name))


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
            fee.approved_by = request.user
            fee.rejection_reason = ""
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
                link="/student/fees",
            )
            return Response({"detail": "Fee rejected."})
        return Response({"detail": "Invalid action."}, status=400)
