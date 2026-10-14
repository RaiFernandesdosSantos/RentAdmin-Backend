"""Cria o plano de contas inicial e as configurações padrão do sistema.

Uso:  python manage.py seed_initial_data [--reset]
--reset desativa (não apaga) as contas existentes e recria o padrão.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from finance.models import ChartAccount
from system.models import SystemSettings

## (código, nome, tipo, classificação, código do pai)
PLAN = [
    # Raízes
    ("1", "RECEITAS", ChartAccount.Type.ENTRIES, ChartAccount.ReportClass.DRE_DFC, None),
    ("2", "DESPESAS", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, None),
    ("3", "NÃO OPERACIONAIS", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DFC_ONLY, None),
    # Grupos de receita
    ("1.1", "Aluguel", ChartAccount.Type.ENTRIES, ChartAccount.ReportClass.DRE_DFC, "1"),
    ("1.2", "Taxas e encargos", ChartAccount.Type.ENTRIES, ChartAccount.ReportClass.DRE_DFC, "1"),
    ("1.3", "Multa e juros", ChartAccount.Type.ENTRIES, ChartAccount.ReportClass.DRE_DFC, "1"),
    ("1.4", "Outras receitas", ChartAccount.Type.ENTRIES, ChartAccount.ReportClass.DRE_DFC, "1"),
    # Contas de receita
    ("1.1.1", "Aluguel residencial", ChartAccount.Type.ENTRIES, ChartAccount.ReportClass.DRE_DFC, "1.1"),
    ("1.1.2", "Aluguel comercial", ChartAccount.Type.ENTRIES, ChartAccount.ReportClass.DRE_DFC, "1.1"),
    ("1.1.3", "Aluguel de terreno", ChartAccount.Type.ENTRIES, ChartAccount.ReportClass.DRE_DFC, "1.1"),
    ("1.2.1", "Condomínio repassado", ChartAccount.Type.ENTRIES, ChartAccount.ReportClass.DRE_DFC, "1.2"),
    ("1.2.2", "Taxa de administração recebida", ChartAccount.Type.ENTRIES, ChartAccount.ReportClass.DRE_DFC, "1.2"),
    ("1.3.1", "Multa por atraso", ChartAccount.Type.ENTRIES, ChartAccount.ReportClass.DRE_DFC, "1.3"),
    ("1.3.2", "Juros de mora", ChartAccount.Type.ENTRIES, ChartAccount.ReportClass.DRE_DFC, "1.3"),
    ("1.4.1", "Receitas diversas", ChartAccount.Type.ENTRIES, ChartAccount.ReportClass.DRE_DFC, "1.4"),
    # Grupos de despesa
    ("2.1", "Impostos e taxas", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2"),
    ("2.2", "Condomínio", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2"),
    ("2.3", "Manutenção e reparos", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2"),
    ("2.4", "Taxas administrativas", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2"),
    ("2.5", "Seguros", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2"),
    ("2.6", "Outras despesas", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2"),
    # Contas de despesa
    ("2.1.1", "IPTU", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2.1"),
    ("2.1.2", "ITBI", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2.1"),
    ("2.1.3", "Taxas municipais", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2.1"),
    ("2.2.1", "Condomínio mensal", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2.2"),
    ("2.3.1", "Reparos emergenciais", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2.3"),
    ("2.3.2", "Pintura e acabamento", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2.3"),
    ("2.3.3", "Reformas", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2.3"),
    ("2.4.1", "Taxa de administração", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2.4"),
    ("2.4.2", "Contabilidade", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2.4"),
    ("2.5.1", "Seguro do imóvel", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2.5"),
    ("2.6.1", "Despesas diversas", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DRE_DFC, "2.6"),
    # Não operacionais (apenas DFC)
    ("3.1", "Aquisição de imóveis", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DFC_ONLY, "3"),
    ("3.1.1", "Compra de imóveis", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DFC_ONLY, "3.1"),
    ("3.1.2", "Escritura e registro", ChartAccount.Type.EXPENSES, ChartAccount.ReportClass.DFC_ONLY, "3.1"),
]

DEFAULT_RENT_ACCOUNT = "1.1.1"


class Command(BaseCommand):
    help = "Cria o plano de contas inicial e as configurações padrão."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Desativa as contas existentes e recria o plano padrão.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            ChartAccount.objects.update(is_active=False)
            self.stdout.write("Contas existentes desativadas.")

        parents = {}
        created_count = 0

        # primeira passada: raízes; segunda: filhos (para respeitar o pai)
        for pass_num in (1, 2):
            for code, name, acc_type, report_class, parent_code in PLAN:
                has_parent = parent_code is not None
                if (pass_num == 1 and has_parent) or (pass_num == 2 and not has_parent):
                    continue
                parent = parents.get(parent_code) if parent_code else None
                account, created = ChartAccount.objects.update_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "type": acc_type,
                        "report_classification": report_class,
                        "parent": parent,
                        "is_active": True,
                    },
                )
                parents[code] = account
                if created:
                    created_count += 1

        # configura a conta padrão de aluguel nas configurações do sistema
        settings = SystemSettings.get()
        rent_account = ChartAccount.objects.filter(code=DEFAULT_RENT_ACCOUNT).first()
        if rent_account and not settings.default_rent_chart_account:
            settings.default_rent_chart_account = rent_account
            settings.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Conta padrão de aluguel definida: {rent_account}"
                )
            )

        total = ChartAccount.objects.filter(is_active=True).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Plano de contas pronto: {created_count} contas criadas, "
                f"{total} contas ativas."
            )
        )
