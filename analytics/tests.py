"""Smoke tests de analytics — resumo do portfólio, DRE e DFC."""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from contracts.models import Contract
from finance.models import BankAccount, ChartAccount, Transaction
from properties.models import Property
from tenants.models import Tenant


class AnalyticsSmokeTests(TestCase):
    def setUp(self):
        self.bank = BankAccount.objects.create(
            bank_name="Banco", account_number="1", agency_number="1"
        )
        root = ChartAccount.objects.create(
            code="1",
            name="RECEITAS",
            type=ChartAccount.Type.ENTRIES,
            report_classification=ChartAccount.ReportClass.DRE_DFC,
        )
        group = ChartAccount.objects.create(
            code="1.1",
            name="Aluguel",
            type=ChartAccount.Type.ENTRIES,
            report_classification=ChartAccount.ReportClass.DRE_DFC,
            parent=root,
        )
        self.rent = ChartAccount.objects.create(
            code="1.1.1",
            name="Aluguel residencial",
            type=ChartAccount.Type.ENTRIES,
            report_classification=ChartAccount.ReportClass.DRE_DFC,
            parent=group,
        )
        expense_root = ChartAccount.objects.create(
            code="2",
            name="DESPESAS",
            type=ChartAccount.Type.EXPENSES,
            report_classification=ChartAccount.ReportClass.DRE_DFC,
        )
        expense_group = ChartAccount.objects.create(
            code="2.1",
            name="Impostos",
            type=ChartAccount.Type.EXPENSES,
            report_classification=ChartAccount.ReportClass.DRE_DFC,
            parent=expense_root,
        )
        self.iptu = ChartAccount.objects.create(
            code="2.1.1",
            name="IPTU",
            type=ChartAccount.Type.EXPENSES,
            report_classification=ChartAccount.ReportClass.DRE_DFC,
            parent=expense_group,
        )
        self.prop = Property.objects.create(
            description="Casa Jardim Europa",
            street="Rua A",
            number="1",
            neighborhood="B",
            registration="1",
            zip_code="12345678",
            square_meters=Decimal("100"),
            actual_value=Decimal("200000.00"),
            status=Property.Status.RENTED,
        )
        self.vacant_prop = Property.objects.create(
            description="Terreno Vila Nova",
            street="Rua C",
            number="2",
            neighborhood="D",
            registration="2",
            zip_code="87654321",
            square_meters=Decimal("400"),
            actual_value=Decimal("50000.00"),
            status=Property.Status.AVAILABLE,
        )
        self.tenant = Tenant.objects.create(
            name="João",
            cpf="11144477735",
            phone_number="11999999999",
            profession="Engenheiro",
            monthly_income=Decimal("9000.00"),
        )
        self.contract = Contract.objects.create(
            property=self.prop,
            tenant=self.tenant,
            monthly_rent=Decimal("1500.00"),
            due_day=10,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )

        # paga aluguéis de jan a mar de 2026 + um IPTU
        for month in (1, 2, 3):
            Transaction.objects.create(
                description=f"Aluguel {month}/2026",
                status=Transaction.Status.PAID,
                amount=Decimal("1500.00"),
                due_date=date(2026, month, 10),
                payment_date=date(2026, month, 10),
                competence_date=date(2026, month, 1),
                account=self.rent,
                bank_account=self.bank,
                property=self.prop,
                contract=self.contract,
            )
        Transaction.objects.create(
            description="IPTU 2026",
            status=Transaction.Status.PAID,
            amount=Decimal("500.00"),
            due_date=date(2026, 2, 15),
            payment_date=date(2026, 2, 15),
            competence_date=date(2026, 2, 1),
            account=self.iptu,
            bank_account=self.bank,
            property=self.prop,
        )

    def test_summary_endpoint(self):
        response = self.client.get("/analytics/summary?year=2026&month=3")
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(str(body["revenue"]["total"]), "1500.00")
        self.assertEqual(body["vacancy"]["total_properties"], 2)
        self.assertEqual(body["vacancy"]["vacant_count"], 1)
        # ROE: 1500*12/200000 = 9%
        self.assertEqual(body["roe"]["average_roe"], 9.0)
        roe_props = [p for p in body["roe"]["properties"]]
        self.assertEqual(len(roe_props), 2)  # alugado + vago

    def test_dre_endpoint(self):
        response = self.client.get("/analytics/dre/?year=2026&month=3")
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(str(body["total_revenue"]), "1500.00")
        self.assertEqual(str(body["total_expenses"]), "0.00")
        self.assertEqual(str(body["net_result"]), "1500.00")

    def test_dfc_endpoint(self):
        response = self.client.get("/analytics/dfc/?year=2026&month=2")
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        # entradas de fev: 1500 aluguel; saídas: 500 IPTU
        self.assertEqual(str(body["total_inflows"]), "1500.00")
        self.assertEqual(str(body["total_outflows"]), "500.00")

    def test_expiring_and_default_endpoints(self):
        response = self.client.get("/analytics/expiring?days=400")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["tenant_name"], "João")

        response = self.client.get("/analytics/default?year=2026")
        self.assertEqual(response.status_code, 200)
        self.assertIn("default_rate", response.json())
