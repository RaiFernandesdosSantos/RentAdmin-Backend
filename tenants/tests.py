"""Testes do módulo de inquilinos — CRUD via API (usado pelos botões
Editar/Excluir da tela de inquilinos)."""
from decimal import Decimal

from django.test import TestCase

from contracts.models import Contract
from finance.models import BankAccount, ChartAccount, Transaction
from properties.models import Property
from tenants.models import Tenant

PAYLOAD = {
    "name": "João Silva",
    "cpf": "11144477735",
    "email": "joao@example.com",
    "phone_number": "11999999999",
    "guarantor": False,
    "profession": "Engenheiro",
    "monthly_income": "9000.00",
    "zip_code": "01234000",
    "street": "Rua A",
    "number": "10",
    "neighborhood": "Centro",
}


class TenantAPITests(TestCase):
    BASE = "/tenants"

    def create_tenant(self, **overrides):
        payload = dict(PAYLOAD)
        payload.update(overrides)
        return self.client.post(
            f"{self.BASE}/create/", payload, content_type="application/json"
        )

    def test_create_and_retrieve(self):
        response = self.create_tenant()
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertIn("id", body)
        self.assertEqual(body["name"], "João Silva")

        detail = self.client.get(f"{self.BASE}/{body['id']}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["cpf"], "11144477735")

    def test_create_rejects_invalid_cpf(self):
        response = self.create_tenant(cpf="11111111111")
        self.assertEqual(response.status_code, 400)

    def test_update_via_patch(self):
        created = self.create_tenant().json()
        response = self.client.patch(
            f"{self.BASE}/{created['id']}/",
            {"phone_number": "11888877777"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            Tenant.objects.get(id=created["id"]).phone_number, "11888877777"
        )

    def test_delete_tenant_without_contracts(self):
        created = self.create_tenant().json()
        response = self.client.delete(f"{self.BASE}/{created['id']}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Tenant.objects.filter(id=created["id"]).exists())

    def test_delete_tenant_cascades_contract(self):
        """Excluir inquilino remove seus contratos (as cobranças ficam)."""
        created = self.create_tenant().json()
        bank = BankAccount.objects.create(
            bank_name="Banco", account_number="1", agency_number="1"
        )
        rent = ChartAccount.objects.create(
            code="1.1.1",
            name="Aluguel",
            type=ChartAccount.Type.ENTRIES,
            report_classification=ChartAccount.ReportClass.DRE_DFC,
        )
        prop = Property.objects.create(
            description="Casa",
            street="R",
            number="1",
            neighborhood="N",
            registration="1",
            zip_code="12345678",
            square_meters=Decimal("100"),
        )
        contract = Contract.objects.create(
            property=prop,
            tenant_id=created["id"],
            monthly_rent=Decimal("1500.00"),
            due_day=10,
            start_date="2026-01-01",
            end_date="2026-12-31",
        )
        Transaction.objects.create(
            description="Aluguel 01/2026",
            status=Transaction.Status.PAID,
            amount=Decimal("1500.00"),
            due_date="2026-01-10",
            payment_date="2026-01-10",
            competence_date="2026-01-01",
            account=rent,
            bank_account=bank,
            contract=contract,
        )

        response = self.client.delete(f"{self.BASE}/{created['id']}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Contract.objects.filter(id=contract.id).exists())
        # a cobrança permanece, desvinculada do contrato (SET_NULL)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertIsNone(Transaction.objects.first().contract)
