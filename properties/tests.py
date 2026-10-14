"""Testes do módulo de Imóveis (Tarefa: Testar módulo de imóveis).

Cobrem: validações do modelo (CEP), normalização do CEP no serializer,
CRUD completo via API, endpoint de venda e importação em lote.
"""
import os
from datetime import date
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from properties.models import Property

PAYLOAD = {
    "description": "Casa Jardim Europa",
    "property_type": Property.PropertyType.RESIDENCIAL,
    "street": "Rua das Flores",
    "number": "120",
    "neighborhood": "Jardim Europa",
    "registration": "12345",
    "zip_code": "12.345-678",
    "square_meters": "120.50",
    "number_of_bedrooms": 3,
    "number_of_bathrooms": 2,
    "garage_spaces": 1,
    "status": Property.Status.AVAILABLE,
    "acquisition_price": "250000.00",
    "acquisition_date": "2022-03-15",
    "actual_value": "300000.00",
}


class PropertyModelTests(TestCase):
    def test_str_returns_description(self):
        prop = Property.objects.create(
            description="Apartamento Centro",
            street="Rua A",
            number="10",
            neighborhood="Centro",
            registration="1",
            zip_code="12345678",
            square_meters=Decimal("50.00"),
        )
        self.assertEqual(str(prop), "Apartamento Centro")

    def test_defaults(self):
        prop = Property.objects.create(
            description="Terreno",
            street="Rua B",
            number="1",
            neighborhood="Zona Rural",
            registration="2",
            zip_code="12345678",
            square_meters=Decimal("100"),
        )
        self.assertEqual(prop.property_type, Property.PropertyType.LAND)
        self.assertEqual(prop.status, Property.Status.AVAILABLE)
        self.assertIsNone(prop.sold_price)
        self.assertIsNone(prop.sold_date)

    def test_zip_mask_fails_full_clean(self):
        """CEP com máscara tem 9 caracteres e não cabe no campo."""
        prop = Property(
            description="X",
            street="R",
            number="1",
            neighborhood="N",
            registration="1",
            zip_code="12345-67",
            square_meters=Decimal("10"),
        )
        with self.assertRaises(Exception):
            prop.full_clean()


class PropertyAPITests(TestCase):
    BASE = "/properties"

    def create_property(self, **overrides):
        payload = dict(PAYLOAD)
        payload.update(overrides)
        return self.client.post(
            f"{self.BASE}/create/", payload, content_type="application/json"
        )

    def test_create_normalizes_zip_code(self):
        response = self.create_property()
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertEqual(body["zip_code"], "12345678")  # sem máscara
        prop = Property.objects.get(id=body["id"])
        self.assertEqual(prop.description, "Casa Jardim Europa")
        self.assertEqual(prop.acquisition_price, Decimal("250000.00"))
        self.assertEqual(prop.acquisition_date, date(2022, 3, 15))

    def test_create_rejects_bad_zip(self):
        response = self.create_property(zip_code="123")
        self.assertEqual(response.status_code, 400)
        self.assertIn("CEP", str(response.json()))

    def test_create_requires_mandatory_fields(self):
        response = self.client.post(
            f"{self.BASE}/create/",
            {"description": "Sem campos"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_list(self):
        self.create_property()
        self.create_property(description="Casa Vila Nova", registration="999")
        response = self.client.get(f"{self.BASE}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        names = [p["description"] for p in response.json()]
        self.assertEqual(names, sorted(names))  # ordenado por descrição

    def test_retrieve(self):
        created = self.create_property().json()
        response = self.client.get(f"{self.BASE}/{created['id']}/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["id"], created["id"])
        self.assertIn("created_at", body)
        self.assertIn("updated_at", body)

    def test_partial_update(self):
        created = self.create_property().json()
        response = self.client.patch(
            f"{self.BASE}/{created['id']}/",
            {"status": Property.Status.MAINTENANCE},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            Property.objects.get(id=created["id"]).status,
            Property.Status.MAINTENANCE,
        )

    def test_update_rejects_bad_zip(self):
        created = self.create_property().json()
        response = self.client.patch(
            f"{self.BASE}/{created['id']}/",
            {"zip_code": "12"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_delete(self):
        created = self.create_property().json()
        response = self.client.delete(f"{self.BASE}/{created['id']}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Property.objects.filter(id=created["id"]).exists())

    def test_sold_endpoint(self):
        created = self.create_property().json()
        response = self.client.patch(
            f"{self.BASE}/{created['id']}/sold/",
            {"sold_price": "350000.00", "sold_date": "2026-10-01"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        prop = Property.objects.get(id=created["id"])
        self.assertEqual(prop.status, Property.Status.SOLD)
        self.assertEqual(prop.sold_price, Decimal("350000.00"))
        self.assertEqual(prop.sold_date, date(2026, 10, 1))

    def test_sold_requires_price_and_date(self):
        created = self.create_property().json()
        response = self.client.patch(
            f"{self.BASE}/{created['id']}/sold/",
            {"sold_price": "350000.00"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


class ImportPropertiesTests(TestCase):
    CSV = (
        "descricao,tipo,rua,numero,bairro,cep,matricula,preco_aquisicao,"
        "data_aquisicao,valor_atual,area_m2,quartos,banheiros,vagas,status\n"
        "Casa 1,residencial,Rua A,10,Centro,12345678,100,250000.00,15/03/2022,"
        "300000.00,120,3,2,1,alugado\n"
        "Terreno 2,terreno,Rua B,20,Borda,87654321,200,80000,2021-06-20,"
        "110000.00,450,,,,disponivel\n"
    )

    def test_import_creates_properties(self):
        tmp = os.path.join(os.environ.get("TMPDIR", "."), "test_import.csv")
        with open(tmp, "w", encoding="utf-8", newline="") as fh:
            fh.write(self.CSV)
        call_command("import_properties", file=tmp)

        casa = Property.objects.get(description="Casa 1")
        self.assertEqual(casa.property_type, Property.PropertyType.RESIDENCIAL)
        self.assertEqual(casa.status, Property.Status.RENTED)
        self.assertEqual(casa.acquisition_date, date(2022, 3, 15))
        self.assertEqual(casa.acquisition_price, Decimal("250000.00"))

        terreno = Property.objects.get(description="Terreno 2")
        self.assertEqual(terreno.property_type, Property.PropertyType.LAND)
        self.assertEqual(terreno.status, Property.Status.AVAILABLE)
        os.remove(tmp)

    def test_import_skips_duplicates(self):
        tmp = os.path.join(os.environ.get("TMPDIR", "."), "test_import_dup.csv")
        with open(tmp, "w", encoding="utf-8", newline="") as fh:
            fh.write(self.CSV)
        call_command("import_properties", file=tmp)
        call_command("import_properties", file=tmp)
        self.assertEqual(Property.objects.count(), 2)
        os.remove(tmp)
