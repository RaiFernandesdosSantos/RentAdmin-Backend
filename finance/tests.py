"""Testes do financeiro — contas bancárias, lançamentos, extrato e
cobranças por e-mail."""
from datetime import date, timedelta
from decimal import Decimal

from django.core import mail
from django.test import TestCase

from contracts.models import Contract
from contracts.service import create_rent_charges
from finance import collections
from finance.models import BankAccount, ChartAccount, Transaction
from properties.models import Property
from tenants.models import Tenant


def make_base():
    bank = BankAccount.objects.create(
        bank_name="Banco Teste", account_number="123", agency_number="1"
    )
    rent = ChartAccount.objects.create(
        code="1.1.1",
        name="Aluguel residencial",
        type=ChartAccount.Type.ENTRIES,
        report_classification=ChartAccount.ReportClass.DRE_DFC,
    )
    prop = Property.objects.create(
        description="Casa Jardim Europa",
        street="Rua das Flores",
        number="120",
        neighborhood="Jardim Europa",
        registration="12345",
        zip_code="12345678",
        square_meters=Decimal("120.00"),
    )
    tenant = Tenant.objects.create(
        name="João Silva",
        cpf="11144477735",
        email="joao@example.com",
        phone_number="11999999999",
        profession="Engenheiro",
        monthly_income=Decimal("9000.00"),
    )
    return bank, rent, prop, tenant


class BankAccountTests(TestCase):
    def test_create_bank_account_with_initial_balance(self):
        response = self.client.post(
            "/finance/bank_account/create/",
            {
                "bank_name": "Itaú",
                "account_number": "1234",
                "agency_number": "0001",
                "initial_balance": "5000.00",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        account = BankAccount.objects.get(
            bank_name="Itaú", account_number="1234", agency_number="0001"
        )
        entries = account.entries.all()
        self.assertEqual(entries.count(), 1)
        self.assertIsNone(entries[0].transaction)
        self.assertEqual(entries[0].balance_after, Decimal("5000.00"))
        self.assertIsNotNone(entries[0].entry_date)

    def test_list_shows_current_balance(self):
        self.client.post(
            "/finance/bank_account/create/",
            {
                "bank_name": "Itaú",
                "account_number": "1234",
                "agency_number": "0001",
                "initial_balance": "5000.00",
            },
            content_type="application/json",
        )
        response = self.client.get("/finance/bank_account/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["current_balance"], "5000.00")
        self.assertIn("monthly_inflows", response.json()[0])
        self.assertIn("monthly_outflows", response.json()[0])


class TransactionEntryTests(TestCase):
    def setUp(self):
        self.bank, self.rent, self.prop, self.tenant = make_base()

    def payload(self, **overrides):
        data = {
            "description": "Aluguel - Casa Jardim Europa",
            "status": "PENDING",
            "amount": "1500.00",
            "due_date": "2026-10-10",
            "payment_date": None,
            "competence_date": "2026-10-01",
            "account": self.rent.id,
            "bank_account": self.bank.id,
        }
        data.update(overrides)
        return data

    def test_paid_transaction_creates_bank_entry(self):
        created = self.client.post(
            "/finance/bank_account/create/",
            {
                "bank_name": "Itaú",
                "account_number": "1234",
                "agency_number": "0001",
                "initial_balance": "5000.00",
            },
            content_type="application/json",
        )
        self.assertEqual(created.status_code, 201, created.content)
        bank_id = created.json()["id"]

        response = self.client.post(
            "/finance/transactions/create/",
            self.payload(
                status="PAID", payment_date="2026-10-10", bank_account=bank_id
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)

        transaction = Transaction.objects.get(id=response.json()["id"])
        entry = transaction.entries.get()
        self.assertEqual(entry.balance_before, Decimal("5000.00"))
        self.assertEqual(entry.balance_after, Decimal("6500.00"))
        self.assertIsNotNone(entry.entry_date)

    def test_pending_transaction_has_no_bank_entry(self):
        response = self.client.post(
            "/finance/transactions/create/",
            self.payload(),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        transaction = Transaction.objects.get(id=response.json()["id"])
        self.assertEqual(transaction.entries.count(), 0)

    def test_patching_to_paid_creates_entry_and_updates_balance(self):
        created = self.client.post(
            "/finance/transactions/create/",
            self.payload(),
            content_type="application/json",
        ).json()

        response = self.client.patch(
            f"/finance/transactions/{created['id']}/",
            {"status": "PAID", "payment_date": "2026-10-10"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        transaction = Transaction.objects.get(id=created["id"])
        self.assertEqual(transaction.entries.count(), 1)

        # desmarca o pagamento -> entrada é removida
        response = self.client.patch(
            f"/finance/transactions/{created['id']}/",
            {"status": "PENDING", "payment_date": None},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        transaction.refresh_from_db()
        self.assertEqual(transaction.entries.count(), 0)

    def test_list_filters_by_account_type_and_status(self):
        self.client.post(
            "/finance/transactions/create/", self.payload(), content_type="application/json"
        )
        expense = ChartAccount.objects.create(
            code="2.1.1",
            name="IPTU",
            type=ChartAccount.Type.EXPENSES,
            report_classification=ChartAccount.ReportClass.DRE_DFC,
        )
        self.client.post(
            "/finance/transactions/create/",
            self.payload(description="IPTU", account=expense.id),
            content_type="application/json",
        )

        response = self.client.get("/finance/transactions/?account_type=ENTRIES")
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["description"], "Aluguel - Casa Jardim Europa")

        response = self.client.get("/finance/transactions/?status=PENDING")
        self.assertEqual(len(response.json()), 2)


class CollectionsTests(TestCase):
    def setUp(self):
        self.bank, self.rent, self.prop, self.tenant = make_base()
        self.contract = Contract.objects.create(
            property=self.prop,
            tenant=self.tenant,
            monthly_rent=Decimal("1500.00"),
            due_day=10,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        create_rent_charges(self.contract)  # mesmo comportamento da API

    def overdue_charge(self):
        today = date.today()
        return Transaction.objects.filter(contract=self.contract).filter(
            due_date__lt=today
        ).order_by("due_date").first()

    def test_mark_overdue_flips_past_due_charges(self):
        today = date.today()
        expected = Transaction.objects.filter(
            contract=self.contract, due_date__lt=today
        ).count()
        self.assertGreater(expected, 0)

        marked = collections.mark_overdue_transactions(today)
        self.assertEqual(marked, expected)
        statuses = set(
            Transaction.objects.filter(
                contract=self.contract, due_date__lt=today
            ).values_list("status", flat=True)
        )
        self.assertEqual(statuses, {Transaction.Status.OVERDUE})

    def test_overdue_listing_includes_tenant_data(self):
        charge = self.overdue_charge()
        charge.status = Transaction.Status.OVERDUE
        charge.save()

        data = collections.get_overdue_charges()
        self.assertTrue(any(c["transaction_id"] == charge.id for c in data))
        item = next(c for c in data if c["transaction_id"] == charge.id)
        self.assertEqual(item["tenant_name"], "João Silva")
        self.assertEqual(item["tenant_email"], "joao@example.com")
        self.assertEqual(item["property_description"], "Casa Jardim Europa")
        self.assertGreaterEqual(item["days_late"], 1)

    def test_collection_email_build_and_send(self):
        charge = self.overdue_charge()
        charge.status = Transaction.Status.OVERDUE
        charge.save()

        email = collections.build_collection_email(charge)
        self.assertEqual(email["to"], "joao@example.com")
        self.assertIn("Cobrança de aluguel", email["subject"])
        self.assertIn("João Silva", email["body"])
        self.assertIn("R$ 1.500,00", email["body"])

        result = collections.send_collection_email(charge)
        self.assertTrue(result["sent"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["joao@example.com"])

    def test_send_email_without_tenant_email_returns_400(self):
        self.tenant.email = None
        self.tenant.save()
        charge = self.overdue_charge()
        charge.status = Transaction.Status.OVERDUE
        charge.save()

        response = self.client.post(f"/finance/collections/{charge.id}/send-email/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("e-mail", response.json()["detail"])

    def test_overdue_endpoint_groups_data(self):
        charge = self.overdue_charge()
        charge.status = Transaction.Status.OVERDUE
        charge.save()

        response = self.client.get("/finance/collections/overdue/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreaterEqual(body["count"], 1)
        self.assertTrue(
            all(c["tenant_name"] == "João Silva" for c in body["charges"])
        )
        self.assertTrue(
            any(c["transaction_id"] == charge.id for c in body["charges"])
        )

        preview = self.client.get(
            f"/finance/collections/{charge.id}/email-preview/"
        )
        self.assertEqual(preview.status_code, 200)
        self.assertIn("subject", preview.json())
