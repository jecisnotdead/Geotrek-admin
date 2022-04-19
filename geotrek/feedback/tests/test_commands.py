from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from geotrek.feedback.models import PendingEmail, PendingSuricateAPIRequest, Report
from geotrek.feedback.tests.factories import ReportFactory


class TestRemoveEmailsOlders(TestCase):
    """Test command erase_emails, if older emails are removed"""
    @classmethod
    def setUpTestData(cls):
        cls.recent_report = ReportFactory(email="yeah@you.com")

    def setUp(self):
        # Create two reports
        self.old_report = ReportFactory(email="to_erase@you.com")
        # Modify date_insert for old_report
        one_year_one_day = timezone.timedelta(days=370)
        self.old_report.date_insert = timezone.now() - one_year_one_day
        self.old_report.save()

    def test_erase_old_emails(self):
        output = StringIO()
        call_command('erase_emails', stdout=output)
        old_report = Report.objects.get(id=self.old_report.id)
        self.assertEqual(old_report.email, "")
        self.assertEqual(old_report.__str__(), f"Report {old_report.pk}")

    def test_dry_run_command(self):
        """Test if dry_run mode keeps emails"""
        output = StringIO()
        call_command('erase_emails', dry_run=True, stdout=output)
        old_report = Report.objects.get(id=self.old_report.id)
        self.assertEqual(old_report.email, "to_erase@you.com")


class TestFlushPendingRequests(TestCase):
    def test_flush_all(self):
        PendingSuricateAPIRequest.objects.create(params="{}")
        PendingEmail.objects.create()
        self.assertEquals(PendingSuricateAPIRequest.objects.count(), 1)
        self.assertEquals(PendingEmail.objects.count(), 1)
        call_command('retry_failed_requests_and_mails', flush=True)
        self.assertEquals(PendingSuricateAPIRequest.objects.count(), 0)
        self.assertEquals(PendingEmail.objects.count(), 0)
