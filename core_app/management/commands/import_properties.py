"""Importa imóveis em lote a partir de um arquivo CSV.

Colunas aceitas (cabeçalho na primeira linha, ; ou , como separador):
    descricao,tipo,rua,numero,bairro,cep,matricula,preco_aquisicao,
    data_aquisicao,valor_atual,area_m2,quartos,banheiros,vagas,status

- tipo: terreno|residencial|comercial (ou 0|1|2)
- status: disponivel|alugado|manutencao|vendido (ou 0|1|2|3)
- datas: AAAA-MM-DD ou DD/MM/AAAA
- CEP: com ou sem máscara
- números com vírgula decimal são aceitos ("150.000,50")

Uso:
    python manage.py import_properties --file imoveis.csv [--dry-run]
"""
import csv
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError

from properties.models import Property

TYPE_MAP = {
    "terreno": Property.PropertyType.LAND,
    "land": Property.PropertyType.LAND,
    "residencial": Property.PropertyType.RESIDENCIAL,
    "comercial": Property.PropertyType.COMERCIAL,
}
STATUS_MAP = {
    "disponivel": Property.Status.AVAILABLE,
    "disponível": Property.Status.AVAILABLE,
    "available": Property.Status.AVAILABLE,
    "alugado": Property.Status.RENTED,
    "rented": Property.Status.RENTED,
    "manutencao": Property.Status.MAINTENANCE,
    "manutenção": Property.Status.MAINTENANCE,
    "vendido": Property.Status.SOLD,
    "sold": Property.Status.SOLD,
}

FIELD_MAP = {
    "descricao": "description",
    "descrição": "description",
    "tipo": "property_type",
    "rua": "street",
    "numero": "number",
    "número": "number",
    "bairro": "neighborhood",
    "cep": "zip_code",
    "matricula": "registration",
    "matrícula": "registration",
    "preco_aquisicao": "acquisition_price",
    "preço_aquisicao": "acquisition_price",
    "data_aquisicao": "acquisition_date",
    "data_aquisição": "acquisition_date",
    "valor_atual": "actual_value",
    "area_m2": "square_meters",
    "área_m2": "square_meters",
    "quartos": "number_of_bedrooms",
    "banheiros": "number_of_bathrooms",
    "vagas": "garage_spaces",
    "status": "status",
}


def _parse_decimal(value):
    if value is None or value.strip() == "":
        return None
    cleaned = re.sub(r"[R$\s]", "", value.strip())
    # 150.000,50 -> 150000.50 ; 150000.50 -> 150000.50 ; 150000 -> 150000
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        raise CommandError(f"Valor numérico inválido: {value!r}")


def _parse_date(value):
    if value is None or value.strip() == "":
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise CommandError(f"Data inválida: {value!r} (use AAAA-MM-DD ou DD/MM/AAAA)")


def _parse_int(value):
    if value is None or value.strip() == "":
        return None
    try:
        return int(value.strip())
    except ValueError:
        raise CommandError(f"Número inteiro inválido: {value!r}")


def _parse_enum(value, mapping, choices, label):
    if value is None or value.strip() == "":
        return None
    key = value.strip().lower()
    if key in mapping:
        return mapping[key]
    try:
        as_int = int(key)
        if as_int in [c[0] for c in choices]:
            return as_int
    except ValueError:
        pass
    raise CommandError(
        f"{label} inválido: {value!r} (opções: {', '.join(mapping.keys())})"
    )


class Command(BaseCommand):
    help = "Importa imóveis a partir de um arquivo CSV."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Caminho do arquivo CSV")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Valida o arquivo sem gravar nada no banco.",
        )

    def handle(self, *args, **options):
        path = options["file"]
        dry_run = options["dry_run"]

        try:
            with open(path, encoding="utf-8-sig", newline="") as fh:
                sample = fh.read(4096)
                fh.seek(0)
                dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
                reader = csv.DictReader(fh, dialect=dialect)
                rows = [
                    {(k or "").strip().lower(): v for k, v in row.items()}
                    for row in reader
                ]
        except FileNotFoundError:
            raise CommandError(f"Arquivo não encontrado: {path}")
        except csv.Error as exc:
            raise CommandError(f"Falha ao ler o CSV: {exc}")

        if not rows:
            raise CommandError("O arquivo não contém linhas de dados.")

        existing = set(
            Property.objects.values_list("description", "street", "number")
        )

        imported, skipped, errors = 0, 0, []
        to_create = []

        for idx, row in enumerate(rows, start=2):
            try:
                data = {}
                for csv_key, model_key in FIELD_MAP.items():
                    raw = row.get(csv_key)
                    if raw is None:
                        continue
                    raw = raw.strip()
                    if raw == "":
                        continue
                    if model_key in (
                        "acquisition_price",
                        "actual_value",
                        "square_meters",
                    ):
                        data[model_key] = _parse_decimal(raw)
                    elif model_key == "acquisition_date":
                        data[model_key] = _parse_date(raw)
                    elif model_key in (
                        "number_of_bedrooms",
                        "number_of_bathrooms",
                        "garage_spaces",
                    ):
                        data[model_key] = _parse_int(raw)
                    elif model_key == "property_type":
                        data[model_key] = _parse_enum(
                            raw, TYPE_MAP, Property.PropertyType.choices, "Tipo"
                        )
                    elif model_key == "status":
                        data[model_key] = _parse_enum(
                            raw, STATUS_MAP, Property.Status.choices, "Status"
                        )
                    elif model_key == "zip_code":
                        digits = re.sub(r"\D", "", raw)
                        if len(digits) != 8:
                            raise CommandError(
                                f"CEP inválido na linha {idx}: {raw!r}"
                            )
                        data[model_key] = digits
                    else:
                        data[model_key] = raw

                for required in ("description", "street", "number", "neighborhood",
                                 "registration", "square_meters"):
                    if required not in data:
                        raise CommandError(
                            f"Coluna obrigatória ausente na linha {idx}: {required}"
                        )

                key = (data["description"], data["street"], data["number"])
                if key in existing:
                    skipped += 1
                    continue

                data.setdefault("property_type", Property.PropertyType.LAND)
                data.setdefault("status", Property.Status.AVAILABLE)
                to_create.append(Property(**data))
                existing.add(key)
                imported += 1
            except CommandError as exc:
                errors.append(str(exc))

        if errors:
            for err in errors:
                self.stdout.write(self.style.ERROR(err))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY-RUN] {imported} imóveis válidos, "
                    f"{skipped} duplicados, {len(errors)} erros. Nada foi gravado."
                )
            )
            return

        Property.objects.bulk_create(to_create)
        self.stdout.write(
            self.style.SUCCESS(
                f"{imported} imóveis importados, {skipped} ignorados "
                f"(já cadastrados), {len(errors)} erros."
            )
        )
