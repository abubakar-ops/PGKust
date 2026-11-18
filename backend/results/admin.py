from django.contrib import admin
from django.core.exceptions import PermissionDenied
from .models import SemesterResultBatch, Result, SemesterGPA, CumulativeGPA

@admin.register(SemesterResultBatch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('session', 'semester', 'programme_type', 'status', 'approved_at')
    list_filter = ('status', 'semester', 'programme_type')
    readonly_fields = (
        'session', 'semester', 'programme_type', 'status', 'coordinator_comment',
        'created_at', 'approved_at', 'approved_by',
    )

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.status == SemesterResultBatch.Status.APPROVED:
            return False
        return super().has_delete_permission(request, obj)

    def delete_queryset(self, request, queryset):
        if queryset.filter(status=SemesterResultBatch.Status.APPROVED).exists():
            raise PermissionDenied("Approved result batches are read-only.")
        super().delete_queryset(request, queryset)

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'score', 'grade', 'grade_point', 'batch')
    list_filter = ('grade', 'batch__status')

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.batch.status == SemesterResultBatch.Status.APPROVED:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.batch.status == SemesterResultBatch.Status.APPROVED:
            return False
        return super().has_delete_permission(request, obj)

    def delete_queryset(self, request, queryset):
        if queryset.filter(batch__status=SemesterResultBatch.Status.APPROVED).exists():
            raise PermissionDenied("Results in approved batches are read-only.")
        super().delete_queryset(request, queryset)

admin.site.register(SemesterGPA)
admin.site.register(CumulativeGPA)
