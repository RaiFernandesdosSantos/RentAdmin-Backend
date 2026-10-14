"""Testes das configurações do sistema (singleton + endpoint /settings/)."""
from django.test import TestCase

from system.models import SystemSettings


class SystemSettingsTests(TestCase):
    def test_get_creates_singleton(self):
        settings = SystemSettings.get()
        self.assertEqual(SystemSettings.objects.count(), 1)
        self.assertEqual(settings.pk, 1)

        # sempre a mesma linha
        again = SystemSettings.get()
        self.assertEqual(settings.pk, again.pk)
        self.assertEqual(SystemSettings.objects.count(), 1)

    def test_settings_endpoint_get_and_patch(self):
        response = self.client.get("/settings/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("owner_name", body)
        self.assertIn("default_due_day", body)
        self.assertIn("default_late_fee", body)
        self.assertIn("notify_overdue_charges", body)

        response = self.client.patch(
            "/settings/",
            {
                "owner_name": "Rai Fernandes",
                "owner_cpf": "12345678901",
                "default_late_fee": "10.00",
                "default_interest_rate": "1.00",
                "notify_upcoming_expenses": True,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)

        body = self.client.get("/settings/").json()
        self.assertEqual(body["owner_name"], "Rai Fernandes")
        self.assertEqual(body["default_late_fee"], "10.00")
        self.assertTrue(body["notify_upcoming_expenses"])
        self.assertEqual(SystemSettings.objects.count(), 1)

    def test_system_alias_works(self):
        response = self.client.get("/system/")
        self.assertEqual(response.status_code, 200)
