"""
End-to-end smoke tests for the PGMS API.

Run from backend/:   python manage.py test smoke_tests
(uses an in-memory SQLite DB, see the 'test' switch in pgms/settings.py)
"""
import hashlib
import hmac
import json
import logging
import shutil
import tempfile
from datetime import date
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import CustomUser, StudentProfile, LecturerProfile, AdminProfile
from courses.models import AcademicSession, Programme, Course, CourseAllocation, Enrollment
from fees.models import FeePayment
from notifications.models import Notification
from reports.models import AnnualProgressReport
from results.grading import GradingEngine
from results.models import Result, SemesterResultBatch, CumulativeGPA

PASSWORD = 'Sm0ke-Test-Pass!'
PAYSTACK_TEST_KEY = 'sk_test_smoke'
MEDIA_TMP = tempfile.mkdtemp(prefix='pgms-smoke-')


def make_user(email, role, **extra):
    return CustomUser.objects.create_user(
        email=email, password=PASSWORD, first_name=email.split('@')[0].title(),
        last_name='Test', role=role, **extra)


@override_settings(MEDIA_ROOT=MEDIA_TMP, PAYSTACK_SECRET_KEY=PAYSTACK_TEST_KEY,
                   MAX_CREDIT_UNITS_PER_SEMESTER=6)
class SmokeTest(TestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TMP, ignore_errors=True)

    def setUp(self):
        # Admins
        self.coordinator = make_user('coord@kust.test', CustomUser.Role.ADMIN)
        AdminProfile.objects.create(user=self.coordinator, admin_role=AdminProfile.AdminRole.PG_COORDINATOR)
        self.hod = make_user('hod@kust.test', CustomUser.Role.ADMIN)
        AdminProfile.objects.create(user=self.hod, admin_role=AdminProfile.AdminRole.HOD)

        # Lecturers
        self.lec_user = make_user('lec@kust.test', CustomUser.Role.LECTURER)
        self.lecturer = LecturerProfile.objects.create(
            user=self.lec_user, staff_id='STF001', is_supervisor=True, status='ACTIVE')
        self.other_lec_user = make_user('lec2@kust.test', CustomUser.Role.LECTURER)
        LecturerProfile.objects.create(user=self.other_lec_user, staff_id='STF002', status='ACTIVE')

        # Students
        self.msc_user = make_user('msc@kust.test', CustomUser.Role.STUDENT)
        self.msc = StudentProfile.objects.create(
            user=self.msc_user, programme='MSC', matric_number='MSC/24/001',
            admission_year=2025, status='ACTIVE')
        self.phd_user = make_user('phd@kust.test', CustomUser.Role.STUDENT)
        self.phd = StudentProfile.objects.create(
            user=self.phd_user, programme='PHD', matric_number='PHD/24/001',
            admission_year=2025, status='ACTIVE')

        # Sessions, programmes, courses, allocations
        self.prev_session = AcademicSession.objects.create(
            name='2024/2025', start_date=date(2024, 9, 1), end_date=date(2025, 8, 31),
            department_fee=Decimal('40000'))
        self.session = AcademicSession.objects.create(
            name='2025/2026', is_current=True, start_date=date(2025, 9, 1),
            end_date=date(2026, 8, 31), department_fee=Decimal('50000'))
        msc_prog = Programme.objects.create(name='Computer Science', programme_type='MSC')
        phd_prog = Programme.objects.create(name='Computer Science', programme_type='PHD')
        self.c1 = Course.objects.create(code='CSC801', title='Algorithms', credit_units=3,
                                        semester='FIRST', programme=msc_prog)
        self.c2 = Course.objects.create(code='CSC802', title='Systems', credit_units=3,
                                        semester='FIRST', programme=msc_prog)
        self.c3 = Course.objects.create(code='CSC803', title='Networks', credit_units=3,
                                        semester='FIRST', programme=msc_prog)
        self.phd_course = Course.objects.create(code='CSC901', title='Research Methods', credit_units=3,
                                                semester='FIRST', programme=phd_prog)
        self.a1 = CourseAllocation.objects.create(lecturer=self.lecturer, course=self.c1,
                                                  session=self.session, semester='FIRST')
        self.a2 = CourseAllocation.objects.create(lecturer=self.lecturer, course=self.c2,
                                                  session=self.session, semester='FIRST')
        self.a3 = CourseAllocation.objects.create(lecturer=self.lecturer, course=self.c3,
                                                  session=self.session, semester='FIRST')
        self.a_phd = CourseAllocation.objects.create(lecturer=self.lecturer, course=self.phd_course,
                                                     session=self.session, semester='FIRST')
        self.a_old = CourseAllocation.objects.create(lecturer=self.lecturer, course=self.c1,
                                                     session=self.prev_session, semester='FIRST')

    # ── helpers ────────────────────────────────────────────────────────────
    def client_for(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    def pay_fee(self, student, session=None):
        session = session or self.session
        return FeePayment.objects.create(
            student=student, academic_year=session.name, amount=session.department_fee,
            payment_method='MANUAL', status='APPROVED')

    def webhook(self, reference, amount_kobo):
        body = json.dumps({'event': 'charge.success',
                           'data': {'reference': reference, 'amount': amount_kobo,
                                    'currency': 'NGN', 'id': 123}}).encode()
        sig = hmac.new(PAYSTACK_TEST_KEY.encode(), body, hashlib.sha512).hexdigest()
        return APIClient().post('/api/fees/webhook/paystack/', body, content_type='application/json',
                                HTTP_X_PAYSTACK_SIGNATURE=sig)

    # ── grading ────────────────────────────────────────────────────────────
    def test_grading_handles_fractional_scores(self):
        cases = {69.5: ('B', 4), 70: ('A', 5), 59.5: ('C', 3), 49.5: ('D', 2),
                 45: ('D', 2), 44.5: ('F', 0), 0: ('F', 0), 100: ('A', 5)}
        for score, (grade, gp) in cases.items():
            self.assertEqual(GradingEngine.get_grade(score), grade, score)
            self.assertEqual(GradingEngine.get_grade_point(score), gp, score)

    # ── accounts ───────────────────────────────────────────────────────────
    def test_lecturer_registration_approval_is_hod_only_and_reject_works(self):
        r = APIClient().post('/api/accounts/register/lecturer/', {
            'email': 'new@kust.test', 'first_name': 'New', 'last_name': 'Lec',
            'password': PASSWORD, 'password_confirm': PASSWORD, 'staff_id': 'stf099',
        }, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        profile = LecturerProfile.objects.get(staff_id='STF099')
        # only the HoD was notified
        self.assertTrue(Notification.objects.filter(recipient=self.hod, notification_type='REGISTRATION').exists())
        self.assertFalse(Notification.objects.filter(recipient=self.coordinator).exists())

        url = f'/api/accounts/admin/lecturers/{profile.pk}/approve/'
        self.assertEqual(self.client_for(self.coordinator).post(url, {'action': 'reject'}).status_code, 403)
        r = self.client_for(self.hod).post(url, {'action': 'reject', 'reason': 'Unknown staff ID'})
        self.assertEqual(r.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.status, LecturerProfile.Status.REJECTED)
        self.assertEqual(profile.registration_note, 'Unknown staff ID')

        r = APIClient().post('/api/auth/login/', {'email': 'new@kust.test', 'password': PASSWORD})
        self.assertEqual(r.status_code, 401)
        self.assertIn('not approved', str(r.data))

    def test_student_approval_is_coordinator_only_and_login_works(self):
        pending = StudentProfile.objects.create(
            user=make_user('pending@kust.test', CustomUser.Role.STUDENT), programme='MSC',
            matric_number='MSC/24/099', admission_year=2025)
        url = f'/api/accounts/admin/students/{pending.pk}/approve/'
        self.assertEqual(self.client_for(self.hod).post(url, {'action': 'approve'}).status_code, 403)
        self.assertEqual(self.client_for(self.coordinator).post(url, {'action': 'approve'}).status_code, 200)
        r = APIClient().post('/api/auth/login/', {'email': 'pending@kust.test', 'password': PASSWORD})
        self.assertEqual(r.status_code, 200)
        self.assertIn('access', r.data)

    # ── enrollment ─────────────────────────────────────────────────────────
    def test_enrollment_rules(self):
        c = self.client_for(self.msc_user)
        # no fee paid yet
        r = c.post('/api/courses/enroll/', {'allocation': self.a1.pk})
        self.assertEqual(r.status_code, 403, r.data)
        self.pay_fee(self.msc)
        # wrong programme, past session
        self.assertEqual(c.post('/api/courses/enroll/', {'allocation': self.a_phd.pk}).status_code, 400)
        self.assertEqual(c.post('/api/courses/enroll/', {'allocation': self.a_old.pk}).status_code, 400)
        # within the 6-unit limit, then over it
        self.assertEqual(c.post('/api/courses/enroll/', {'allocation': self.a1.pk}).status_code, 201)
        self.assertEqual(c.post('/api/courses/enroll/', {'allocation': self.a2.pk}).status_code, 201)
        r = c.post('/api/courses/enroll/', {'allocation': self.a3.pk})
        self.assertEqual(r.status_code, 400)
        self.assertIn('Credit limit', r.data['detail'])
        # duplicate
        self.assertEqual(c.post('/api/courses/enroll/', {'allocation': self.a1.pk}).status_code, 400)

    def test_phd_needs_previous_apr_to_enroll(self):
        self.phd.admission_year = 2024
        self.phd.save()
        self.pay_fee(self.phd)
        c = self.client_for(self.phd_user)
        r = c.post('/api/courses/enroll/', {'allocation': self.a_phd.pk})
        self.assertEqual(r.status_code, 403)
        self.assertIn('Annual Progress Report', r.data['detail'])
        AnnualProgressReport.objects.create(
            student=self.phd, session=self.prev_session, year_of_study=1,
            research_progress='x', training_activities='x', next_year_plan='x',
            status='COORDINATOR_APPROVED', progression_cleared=True)
        self.assertEqual(c.post('/api/courses/enroll/', {'allocation': self.a_phd.pk}).status_code, 201)

    # ── results ────────────────────────────────────────────────────────────
    def test_result_upload_is_scoped_and_publish_notifies_once(self):
        e1 = Enrollment.objects.create(student=self.msc, allocation=self.a1, status='APPROVED')
        e2 = Enrollment.objects.create(student=self.msc, allocation=self.a2, status='APPROVED')
        pending = Enrollment.objects.create(student=self.phd, allocation=self.a3, status='PENDING')

        # another lecturer cannot touch this allocation
        r = self.client_for(self.other_lec_user).post('/api/results/upload/', {
            'allocation': self.a1.pk, 'results': [{'enrollment': e1.pk, 'score': 100}]}, format='json')
        self.assertEqual(r.status_code, 404)
        self.assertFalse(Result.objects.exists())

        lec = self.client_for(self.lec_user)
        # enrollment from a different allocation and a non-approved one are refused
        r = lec.post('/api/results/upload/', {'allocation': self.a1.pk, 'results': [
            {'enrollment': e1.pk, 'score': '69.50'},
            {'enrollment': e2.pk, 'score': 90},
            {'enrollment': pending.pk, 'score': 90},
        ]}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['uploaded'], 1)
        self.assertEqual(len(r.data['errors']), 2)
        self.assertEqual(Result.objects.get(enrollment=e1).grade, 'B')

        lec.post('/api/results/upload/', {'allocation': self.a2.pk,
                                          'results': [{'enrollment': e2.pk, 'score': 75}]}, format='json')
        batch = SemesterResultBatch.objects.get()
        # students can't see pending results
        self.assertEqual(self.client_for(self.msc_user).get('/api/results/mine/').data, [])

        # only the PG Coordinator approves
        url = f'/api/results/batches/{batch.pk}/approve/'
        self.assertEqual(self.client_for(self.hod).post(url, {'action': 'approve'}).status_code, 403)
        self.assertEqual(self.client_for(self.coordinator).post(url, {'action': 'approve'}).status_code, 200)

        self.assertEqual(Notification.objects.filter(recipient=self.msc_user, notification_type='RESULT').count(), 1)
        self.assertEqual(len(self.client_for(self.msc_user).get('/api/results/mine/').data), 2)
        cgpa = CumulativeGPA.objects.get(student=self.msc)
        self.assertEqual(cgpa.cgpa, Decimal('4.50'))  # (4*3 + 5*3) / 6

        # approved batch is locked
        r = lec.post('/api/results/upload/', {'allocation': self.a1.pk,
                                              'results': [{'enrollment': e1.pk, 'score': 10}]}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_transcript_never_500s(self):
        # A 503 is logged by django.request, and Django 4.2's error reporter crashes
        # on Python 3.14 while formatting it — mute that logger for this request.
        request_logger = logging.getLogger('django.request')
        request_logger.disabled = True
        try:
            r = self.client_for(self.msc_user).get('/api/reports/transcript/')
        finally:
            request_logger.disabled = False
        self.assertIn(r.status_code, (200, 503))  # 503 when WeasyPrint's native libs are missing
        if r.status_code == 200:
            self.assertEqual(r['Content-Type'], 'application/pdf')

    # ── fees ───────────────────────────────────────────────────────────────
    def test_manual_fee_amount_is_server_side_and_resubmit_after_reject(self):
        c = self.client_for(self.msc_user)
        self.assertEqual(c.get('/api/fees/status/').data['status'], 'NOT_PAID')
        receipt = SimpleUploadedFile('receipt.pdf', b'%PDF-1.4 receipt', content_type='application/pdf')
        r = c.post('/api/fees/pay/manual/', {'receipt': receipt, 'amount': 1}, format='multipart')
        self.assertEqual(r.status_code, 201, r.data)
        fee = FeePayment.objects.get(student=self.msc)
        self.assertEqual(fee.amount, Decimal('50000'))
        self.assertEqual(fee.academic_year, '2025/2026')
        self.assertTrue(r.data['receipt_file'].startswith('/api/fees/'))

        # receipt is private to its owner and admins
        self.assertEqual(self.client_for(self.phd_user).get(r.data['receipt_file']).status_code, 403)
        self.assertEqual(self.client_for(self.coordinator).get(r.data['receipt_file']).status_code, 200)

        self.client_for(self.coordinator).post(f'/api/fees/admin/{fee.pk}/approve/',
                                               {'action': 'reject', 'reason': 'Blurry'})
        receipt2 = SimpleUploadedFile('receipt2.png', b'\x89PNG fake', content_type='image/png')
        r = c.post('/api/fees/pay/manual/', {'receipt': receipt2}, format='multipart')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(FeePayment.objects.filter(student=self.msc).count(), 1)
        self.assertEqual(r.data['status'], 'PENDING')

    def test_paystack_webhook_rejects_underpayment(self):
        fee = FeePayment.objects.create(student=self.msc, academic_year=self.session.name,
                                        amount=Decimal('50000'), payment_method='ONLINE',
                                        status='PENDING', transaction_reference='ref-1')
        self.assertEqual(self.webhook('ref-1', 100).status_code, 200)  # ₦1
        fee.refresh_from_db()
        self.assertEqual(fee.status, 'PENDING')

        self.assertEqual(self.webhook('ref-1', 5_000_000).status_code, 200)  # ₦50,000
        fee.refresh_from_db()
        self.assertEqual(fee.status, 'APPROVED')

        # bad signature is refused
        r = APIClient().post('/api/fees/webhook/paystack/', {'event': 'charge.success'}, format='json',
                             HTTP_X_PAYSTACK_SIGNATURE='nope')
        self.assertEqual(r.status_code, 400)

    # ── materials ──────────────────────────────────────────────────────────
    def test_material_download_requires_enrollment_and_fee(self):
        upload = SimpleUploadedFile('week1.pdf', b'%PDF-1.4 slides', content_type='application/pdf')
        r = self.client_for(self.lec_user).post(
            f'/api/courses/materials/{self.a1.pk}/upload/',
            {'file': upload, 'title': 'Week 1', 'description': 'Intro'}, format='multipart')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['file'], 'week1.pdf')
        self.assertNotIn('/media/', r.data['download_url'])
        url = r.data['download_url']

        student = self.client_for(self.msc_user)
        self.assertEqual(student.get(url).status_code, 403)  # not enrolled
        Enrollment.objects.create(student=self.msc, allocation=self.a1, status='APPROVED')
        self.assertEqual(student.get(url).status_code, 403)  # fee unpaid
        self.pay_fee(self.msc)
        r = student.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(b''.join(r.streaming_content), b'%PDF-1.4 slides')
        r.close()
        self.assertEqual(self.client_for(self.other_lec_user).get(url).status_code, 403)

    # ── APR ────────────────────────────────────────────────────────────────
    def test_apr_workflow_with_supervisor_assignment_and_resubmission(self):
        phd = self.client_for(self.phd_user)
        r = phd.post('/api/reports/apr/create/', {
            'year_of_study': 1, 'research_progress': 'Lit review', 'training_activities': 'Workshop',
            'next_year_plan': 'Experiments'}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        apr_id = r.data['id']

        # no supervisor yet
        r = phd.post(f'/api/reports/apr/{apr_id}/submit/')
        self.assertEqual(r.status_code, 400)
        self.assertIn('supervisor', r.data['detail'])

        # coordinator assigns one (and can't give an MSc student a supervisor)
        coord = self.client_for(self.coordinator)
        r = coord.patch(f'/api/accounts/admin/students/{self.msc.pk}/', {'supervisor': self.lecturer.pk})
        self.assertEqual(r.status_code, 400)
        r = coord.patch(f'/api/accounts/admin/students/{self.phd.pk}/', {'supervisor': self.lecturer.pk})
        self.assertEqual(r.status_code, 200, r.data)

        self.assertEqual(phd.post(f'/api/reports/apr/{apr_id}/submit/').status_code, 200)
        r = self.client_for(self.lec_user).post(f'/api/reports/apr/{apr_id}/endorse/', {'comments': 'Good'})
        self.assertEqual(r.status_code, 200)
        r = coord.post(f'/api/reports/apr/{apr_id}/approve/', {'action': 'reject', 'comments': 'More detail'})
        self.assertEqual(r.status_code, 200)

        # admins can't PATCH an APR (was a 500)
        self.assertEqual(coord.patch(f'/api/reports/apr/{apr_id}/', {'publications': 'x'}).status_code, 403)

        # rejected APR can be edited and resubmitted
        r = phd.patch(f'/api/reports/apr/{apr_id}/', {'research_progress': 'Lit review + pilot'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['status'], 'DRAFT')
        self.assertEqual(phd.post(f'/api/reports/apr/{apr_id}/submit/').status_code, 200)

        r = phd.get(f'/api/reports/apr/{apr_id}/')
        self.assertEqual(r.data['supervisor_name'], self.lec_user.get_full_name())
        self.assertEqual(len(phd.get('/api/reports/apr/').data), 1)

    # ── regressions found in review ────────────────────────────────────────
    def test_graduated_student_cannot_log_in(self):
        self.msc.status = StudentProfile.Status.GRADUATED
        self.msc.save()
        r = APIClient().post('/api/auth/login/', {'email': 'msc@kust.test', 'password': PASSWORD})
        self.assertEqual(r.status_code, 401)

    def test_long_session_name_fits_fee_record(self):
        self.session.name = '2025/2026 Session'
        self.session.save()
        receipt = SimpleUploadedFile('r.pdf', b'%PDF', content_type='application/pdf')
        r = self.client_for(self.msc_user).post('/api/fees/pay/manual/', {'receipt': receipt}, format='multipart')
        self.assertEqual(r.status_code, 201, r.data)
        field = FeePayment._meta.get_field('academic_year')
        self.assertGreaterEqual(field.max_length, AcademicSession._meta.get_field('name').max_length)

    def test_webhook_matches_superseded_reference_by_metadata(self):
        fee = FeePayment.objects.create(student=self.msc, academic_year=self.session.name,
                                        amount=Decimal('50000'), payment_method='ONLINE',
                                        status='PENDING', transaction_reference='ref-second')
        body = json.dumps({'event': 'charge.success', 'data': {
            'reference': 'ref-first', 'amount': 5_000_000, 'currency': 'NGN', 'id': 9,
            'metadata': {'student_id': self.msc.pk, 'academic_year': self.session.name}}}).encode()
        sig = hmac.new(PAYSTACK_TEST_KEY.encode(), body, hashlib.sha512).hexdigest()
        r = APIClient().post('/api/fees/webhook/paystack/', body, content_type='application/json',
                             HTTP_X_PAYSTACK_SIGNATURE=sig)
        self.assertEqual(r.status_code, 200)
        fee.refresh_from_db()
        self.assertEqual(fee.status, 'APPROVED')
        self.assertEqual(fee.transaction_reference, 'ref-first')

    def test_manual_receipt_allowed_after_abandoned_online_checkout(self):
        FeePayment.objects.create(student=self.msc, academic_year=self.session.name,
                                  amount=Decimal('50000'), payment_method='ONLINE',
                                  status='PENDING', transaction_reference='ref-abandoned')
        receipt = SimpleUploadedFile('r.pdf', b'%PDF', content_type='application/pdf')
        r = self.client_for(self.msc_user).post('/api/fees/pay/manual/', {'receipt': receipt}, format='multipart')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['payment_method'], 'MANUAL')

    def test_apr_can_be_filed_for_previous_session_and_validates_year(self):
        phd = self.client_for(self.phd_user)
        r = phd.post('/api/reports/apr/create/', {'year_of_study': 'two'}, format='json')
        self.assertEqual(r.status_code, 400)
        r = phd.post('/api/reports/apr/create/', {'session': self.prev_session.pk, 'year_of_study': 1,
                                                  'research_progress': None}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['session'], self.prev_session.pk)
        self.assertEqual(r.data['research_progress'], '')
        older = AcademicSession.objects.create(name='2023/2024', start_date=date(2023, 9, 1),
                                               end_date=date(2024, 8, 31))
        r = phd.post('/api/reports/apr/create/', {'session': older.pk}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_batch_reapproval_and_failed_reupload_are_noops(self):
        e1 = Enrollment.objects.create(student=self.msc, allocation=self.a1, status='APPROVED')
        lec = self.client_for(self.lec_user)
        lec.post('/api/results/upload/', {'allocation': self.a1.pk,
                                          'results': [{'enrollment': e1.pk, 'score': 80}]}, format='json')
        batch = SemesterResultBatch.objects.get()
        coord = self.client_for(self.coordinator)
        url = f'/api/results/batches/{batch.pk}/approve/'

        coord.post(url, {'action': 'reject', 'comment': 'fix'})
        # an upload where every row fails must not put the batch back in the queue
        lec.post('/api/results/upload/', {'allocation': self.a1.pk,
                                          'results': [{'enrollment': 999999, 'score': 80}]}, format='json')
        batch.refresh_from_db()
        self.assertEqual(batch.status, 'REJECTED')
        lec.post('/api/results/upload/', {'allocation': self.a1.pk,
                                          'results': [{'enrollment': e1.pk, 'score': 81}]}, format='json')
        batch.refresh_from_db()
        self.assertEqual(batch.status, 'PENDING')

        self.assertEqual(coord.post(url, {'action': 'approve'}).status_code, 200)
        self.assertEqual(coord.post(url, {'action': 'approve'}).status_code, 400)
        self.assertEqual(Notification.objects.filter(recipient=self.msc_user, notification_type='RESULT').count(), 1)

    def test_registration_notifies_all_admins_when_role_missing(self):
        AdminProfile.objects.filter(admin_role='HOD').delete()
        APIClient().post('/api/accounts/register/lecturer/', {
            'email': 'x@kust.test', 'first_name': 'X', 'last_name': 'Y',
            'password': PASSWORD, 'password_confirm': PASSWORD, 'staff_id': 'STF777'}, format='json')
        self.assertTrue(Notification.objects.filter(recipient=self.coordinator).exists())
