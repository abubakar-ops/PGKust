from django.contrib import admin
from .models import AnnualProgressReport

@admin.register(AnnualProgressReport)
class APRAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'year_of_study', 'status', 'progression_cleared', 'submitted_at')
    list_filter = ('status', 'progression_cleared')
    search_fields = ('student__matric_number', 'student__user__first_name')
