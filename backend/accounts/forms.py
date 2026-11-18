from django import forms
from django.contrib.auth.forms import AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import CustomUser, StudentProfile, LecturerProfile


class StudentRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=15, required=False)
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    programme = forms.ChoiceField(choices=StudentProfile.Programme.choices)
    matric_number = forms.CharField(max_length=20)
    admission_year = forms.IntegerField(min_value=2000, max_value=2100)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('first_name', css_class='col-md-6'), Column('last_name', css_class='col-md-6')),
            'email', 'phone_number',
            Row(Column('password', css_class='col-md-6'), Column('confirm_password', css_class='col-md-6')),
            Row(Column('programme', css_class='col-md-4'), Column('matric_number', css_class='col-md-4'), Column('admission_year', css_class='col-md-4')),
            Submit('submit', 'Submit Registration', css_class='btn btn-primary w-100 mt-3'),
        )

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_matric_number(self):
        matric = self.cleaned_data['matric_number'].upper()
        if StudentProfile.objects.filter(matric_number=matric).exists():
            raise forms.ValidationError('This matric number is already registered.')
        return matric

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned


class LecturerRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=15, required=False)
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    staff_id = forms.CharField(max_length=20)
    specialization = forms.CharField(max_length=100, required=False)
    is_supervisor = forms.BooleanField(required=False, label='Available as PhD supervisor')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('first_name', css_class='col-md-6'), Column('last_name', css_class='col-md-6')),
            'email', 'phone_number',
            Row(Column('password', css_class='col-md-6'), Column('confirm_password', css_class='col-md-6')),
            Row(Column('staff_id', css_class='col-md-6'), Column('specialization', css_class='col-md-6')),
            'is_supervisor',
            Submit('submit', 'Submit Registration', css_class='btn btn-success w-100 mt-3'),
        )

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_staff_id(self):
        sid = self.cleaned_data['staff_id'].upper()
        if LecturerProfile.objects.filter(staff_id=sid).exists():
            raise forms.ValidationError('This staff ID is already registered.')
        return sid

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email Address', widget=forms.EmailInput(attrs={'autofocus': True}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username', 'password',
            Submit('submit', 'Sign In', css_class='btn btn-primary w-100 mt-3'),
        )
