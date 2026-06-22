from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, StudentProfile, LecturerProfile, AdminProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'get_full_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = UserAdmin.fieldsets + (('Role', {'fields': ('role', 'phone_number', 'profile_picture')}),)

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('matric_number', 'user', 'programme', 'status', 'admission_year')
    list_filter = ('programme', 'status')
    search_fields = ('matric_number', 'user__first_name', 'user__last_name', 'user__email')
    actions = ['approve_selected']

    def approve_selected(self, request, queryset):
        queryset.update(status='ACTIVE')
    approve_selected.short_description = 'Approve selected students'

@admin.register(LecturerProfile)
class LecturerProfileAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'user', 'specialization', 'is_supervisor', 'status')
    list_filter = ('status', 'is_supervisor')
    search_fields = ('staff_id', 'user__first_name', 'user__last_name')

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'admin_role')
