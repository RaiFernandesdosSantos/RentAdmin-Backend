"""Testes dos contratos — cobranças automáticas, sincronização,
encerramento e emissão de PDF."""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from contracts.models import Contract
from contracts.service import create_rent_charges
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
        actual_value=Decimal("300000.00"),
        status=Property.Status.RENTED,
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


class RentChargesTests(TestCase):
    def setUp(self):
        self.bank, self.rent, self.prop, self.tenant = make_base()

    def create_contract(self, **overrides):
        defaults = dict(
            property=self.prop,
            tenant=self.tenant,
            monthly_rent=Decimal("1500.00"),
            due_day=10,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        defaults.update(overrides)
        contract = Contract.objects.create(**defaults)
        create_rent_charges(contract)  # mesmo comportamento da API
        return contract

    def test_contract_creates_12_monthly_charges(self):
        contract = self.create_contract()
        charges = Transaction.objects.filter(contract=contract)
        self.assertEqual(charges.count(), 12)

        first = charges.order_by("due_date").first()
        self.assertEqual(first.due_date, date(2026, 1, 10))
        self.assertEqual(first.competence_date, date(2026, 1, 1))
        self.assertEqual(first.status, Transaction.Status.PENDING)
        self.assertEqual(first.recurrence, Transaction.Recurrence.MONTHLY)
        self.assertEqual(first.amount, Decimal("1500.00"))
        self.assertIn("Casa Jardim Europa", first.description)
        self.assertEqual(first.account, self.rent)
        self.assertEqual(first.bank_account, self.bank)

        last = charges.order_by("due_date").last()
        self.assertEqual(last.due_date, date(2026, 12, 10))

    def test_due_day_31_clamps_to_last_day_of_february(self):
        contract = self.create_contract(
            due_day=31, start_date=date(2026, 1, 5), end_date=date(2026, 3, 31)
        )
        dues = list(
            Transaction.objects.filter(contract=contract)
            .order_by("due_date")
            .values_list("due_date", flat=True)
        )
        self.assertEqual(dues, [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31)])

    def test_charge_starts_month_after_start_date(self):
        """Início no dia do vencimento -> primeira cobrança no mês seguinte."""
        contract = self.create_contract(start_date=date(2026, 1, 10))
        first = (
            Transaction.objects.filter(contract=contract)
            .order_by("due_date")
            .first()
        )
        self.assertEqual(first.due_date, date(2026, 2, 10))

    def test_api_create_contract_generates_charges(self):
        payload = {
            "property": self.prop.id,
            "tenant": self.tenant.id,
            "monthly_rent": "1500.00",
            "due_day": 10,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        }
        response = self.client.post(
            "/contracts/create/", payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Transaction.objects.count(), 12)

    def test_list_filters_by_tenant_and_property(self):
        other_prop = Property.objects.create(
            description="Casa Vila Nova",
            street="Rua B",
            number="2",
            neighborhood="Vila",
            registration="99",
            zip_code="87654321",
            square_meters=Decimal("80"),
        )
        other_tenant = Tenant.objects.create(
            name="Maria Souza",
            cpf="52998224725",
            phone_number="1188887777",
            profession="Professora",
            monthly_income=Decimal("7000.00"),
        )
        self.create_contract()
        self.create_contract(
            property=other_prop,
            tenant=other_tenant,
            monthly_rent=Decimal("900.00"),
        )

        response = self.client.get(f"/contracts/?tenant={self.tenant.id}")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["tenant"]["name"], "João Silva")

        response = self.client.get(f"/contracts/?property={other_prop.id}")
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["property"]["description"], "Casa Vila Nova")

        response = self.client.get("/contracts/?status=0")
        self.assertEqual(len(response.json()), 2)

    def test_api_rejects_invalid_due_day_and_dates(self):
        payload = {
            "property": self.prop.id,
            "tenant": self.tenant.id,
            "monthly_rent": "1500.00",
            "due_day": 45,
            "start_date": "2026-12-01",
            "end_date": "2026-01-01",
        }
        response = self.client.post(
            "/contracts/create/", payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Contract.objects.count(), 0)

    def test_create_without_bank_account_fails_cleanly(self):
        BankAccount.objects.all().delete()
        payload = {
            "property": self.prop.id,
            "tenant": self.tenant.id,
            "monthly_rent": "1500.00",
            "due_day": 10,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        }
        response = self.client.post(
            "/contracts/create/", payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400, response.content)
        # rollback atômico: o contrato não pode ter persistido
        self.assertEqual(Contract.objects.count(), 0)

    def test_update_contract_syncs_open_charges(self):
        contract = self.create_contract()

        # paga a cobrança de janeiro (histórico deve ser preservado)
        jan = Transaction.objects.get(
            contract=contract, competence_date=date(2026, 1, 1)
        )
        jan.status = Transaction.Status.PAID
        jan.payment_date = jan.due_date
        jan.save()

        response = self.client.patch(
            f"/contracts/{contract.id}/",
            {"monthly_rent": "2000.00", "end_date": "2027-06-30"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)

        charges = Transaction.objects.filter(contract=contract)
        jan.refresh_from_db()
        self.assertEqual(jan.status, Transaction.Status.PAID)
        self.assertEqual(jan.amount, Decimal("1500.00"))  # valor original

        # 02/2026 a 06/2027 regeradas com o valor novo (17 meses)
        open_charges = charges.exclude(status=Transaction.Status.PAID)
        self.assertEqual(open_charges.count(), 17)
        feb = charges.get(competence_date=date(2026, 2, 1))
        self.assertEqual(feb.amount, Decimal("2000.00"))

    def test_close_contract_cancels_open_charges(self):
        contract = self.create_contract()
        response = self.client.post(f"/contracts/{contract.id}/close/")
        self.assertEqual(response.status_code, 200)
        contract.refresh_from_db()
        self.assertEqual(contract.status, Contract.Status.CANCELLED)
        statuses = set(
            Transaction.objects.filter(contract=contract).values_list(
                "status", flat=True
            )
        )
        self.assertEqual(statuses, {Transaction.Status.CANCELLED})


class ContractPdfTests(TestCase):
    def setUp(self):
        self.bank, self.rent, self.prop, self.tenant = make_base()

    def test_contract_pdf_is_generated(self):
        contract = Contract.objects.create(
            property=self.prop,
            tenant=self.tenant,
            monthly_rent=Decimal("1500.00"),
            due_day=10,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        response = self.client.get(f"/contracts/{contract.id}/contract-pdf/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertIn("attachment", response["Content-Disposition"])
