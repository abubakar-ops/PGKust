from django.contrib import admin
from .models import SemesterResultBatch, Result, SemesterGPA, CumulativeGPA

@admin.register(SemesterResultBatch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('session', 'semester', 'programme_type', 'status', 'approved_at')
    list_filter = ('status', 'semester', 'programme_type')

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'score', 'grade', 'grade_point', 'batch')
    list_filter = ('grade', 'batch__status')

admin.site.register(SemesterGPA)
admin.site.register(CumulativeGPA)
