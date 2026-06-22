from django.contrib import admin
from .models import FeePayment

@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'academic_year', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'academic_year')
    search_fields = ('student__matric_number', 'transaction_reference')
