from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin_user)


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_student)


class IsLecturer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_lecturer)


class IsActiveStudent(BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.is_student):
            return False
        try:
            return request.user.student_profile.is_active
        except Exception:
            return False


class IsActiveLecturer(BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.is_lecturer):
            return False
        try:
            return request.user.lecturer_profile.is_active
        except Exception:
            return False


class IsPGCoordinator(BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.is_admin_user):
            return False
        try:
            return request.user.admin_profile.is_pg_coordinator
        except Exception:
            return False


class IsHoD(BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.is_admin_user):
            return False
        try:
            return request.user.admin_profile.is_hod
        except Exception:
            return False
