from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Base mixin that enforces a required user role.
    Subclasses set `required_role` to one of: 'STUDENT', 'LECTURER', 'ADMIN'.
    """
    required_role = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.required_role and request.user.role != self.required_role:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class StudentRequiredMixin(RoleRequiredMixin):
    required_role = 'STUDENT'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated and request.user.role == 'STUDENT':
            profile = getattr(request.user, 'student_profile', None)
            if profile and profile.status != 'ACTIVE':
                return redirect('accounts:pending_approval')
        return response


class LecturerRequiredMixin(RoleRequiredMixin):
    required_role = 'LECTURER'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated and request.user.role == 'LECTURER':
            profile = getattr(request.user, 'lecturer_profile', None)
            if profile and profile.status != 'ACTIVE':
                return redirect('accounts:pending_approval')
        return response


class AdminRequiredMixin(RoleRequiredMixin):
    required_role = 'ADMIN'


class FeeRequiredMixin(StudentRequiredMixin):
    """
    Blocks student access if annual department fee for the current academic year
    has not been approved. Redirects to fee payment page.
    """
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated and request.user.role == 'STUDENT':
            from fees.models import FeePayment
            from courses.models import AcademicSession
            current_session = AcademicSession.objects.filter(is_current=True).first()
            if current_session:
                academic_year = current_session.name
                fee_cleared = FeePayment.objects.filter(
                    student=request.user.student_profile,
                    academic_year=academic_year,
                    status='APPROVED',
                ).exists()
                if not fee_cleared:
                    return redirect('fees:payment_required')
        return response
