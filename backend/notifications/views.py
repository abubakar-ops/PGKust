from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    def get(self, request):
        qs = Notification.objects.filter(recipient=request.user).order_by("-created_at")[:50]
        return Response({
            "count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
            "results": NotificationSerializer(qs, many=True).data,
        })


class MarkReadView(APIView):
    def post(self, request, pk):
        try:
            n = Notification.objects.get(pk=pk, recipient=request.user)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        n.mark_read()
        return Response({"detail": "Marked as read."})


class MarkAllReadView(APIView):
    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({"detail": "All notifications marked as read."})
