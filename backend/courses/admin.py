from django.contrib import admin
from .models import AcademicSession, Programme, Course, CourseAllocation, Timetable, Enrollment, CourseMaterial

admin.site.register(AcademicSession)
admin.site.register(Programme)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'credit_units', 'semester', 'programme', 'is_active')
    list_filter = ('semester', 'programme', 'is_active')
    search_fields = ('code', 'title')

admin.site.register(CourseAllocation)
admin.site.register(Timetable)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'allocation', 'status', 'enrolled_at')
    list_filter = ('status',)

admin.site.register(CourseMaterial)
