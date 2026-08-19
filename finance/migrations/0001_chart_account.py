import django.db.models.deletion
from django.db import migrations, models


def seed_chart_account(apps, schema_editor):
    ChartAccount = apps.get_model("finance", "ChartAccount")

    ativos = ChartAccount.objects.create(
        code="1", name="Ativos", type=0, report_classification=1, parent=None
    )
    passivos = ChartAccount.objects.create(
        code="2", name="Passivos", type=1, report_classification=0, parent=None
    )

    receitas = ChartAccount.objects.create(
        code="3", name="Receitas", type=0, report_classification=0, parent=None
    )

    despesas = ChartAccount.objects.create(
        code="4", name="Despesas", type=1, report_classification=1, parent=None
    )

    aluguel = ChartAccount.objects.create(
        code="3.1",
        name="Receita de Aluguel",
        type=0,
        report_classification=0,
        parent=receitas,
    )

    outras_receitas = ChartAccount.objects.create(
        code="3.2",
        name="Outras Receitas",
        type=1,
        report_classification=0,
        parent=despesas,
    )

    ChartAccount.objects.bulk_create(
        [
            ChartAccount(
                code="3.1.1",
                name="Aluguel Residencial",
                type=0,
                report_classification=0,
                parent=aluguel,
            ),
            ChartAccount(
                code="3.1.2",
                name="Aluguel Comercial",
                type=0,
                report_classification=0,
                parent=aluguel,
            ),
            ChartAccount(
                code="3.2.1",
                name="Multas e Juros Recebidos",
                type=0,
                report_classification=0,
                parent=outras_receitas,
            ),
        ]
    )

    impostos = ChartAccount.objects.create(
        code="4.1", name="Impostos", type=1, report_classification=0, parent=despesas
    )

    operacionais = ChartAccount.objects.create(
        code="4.2",
        name="Despesas Operacionais",
        type=1,
        report_classification=0,
        parent=despesas,
    )

    financeiras = ChartAccount.objects.create(
        code="4.3",
        name="Despesas Financeiras",
        type=1,
        report_classification=0,
        parent=despesas,
    )

    ChartAccount.objects.bulk_create(
        [
            ChartAccount(
                code="4.1.1",
                name="IPTU",
                type=1,
                report_classification=0,
                parent=impostos,
            ),
            ChartAccount(
                code="4.1.2",
                name="Imposto de Renda",
                type=1,
                report_classification=0,
                parent=impostos,
            ),
            ChartAccount(
                code="4.2.1",
                name="Manutenção e Reparos",
                type=1,
                report_classification=0,
                parent=operacionais,
            ),
            ChartAccount(
                code="4.2.2",
                name="Seguro do Imóvel",
                type=1,
                report_classification=0,
                parent=operacionais,
            ),
            ChartAccount(
                code="4.2.3",
                name="Taxa de Administração",
                type=1,
                report_classification=0,
                parent=operacionais,
            ),
            ChartAccount(
                code="4.3.1",
                name="Juros de Financiamento",
                type=1,
                report_classification=1,
                parent=financeiras,
            ),
        ]
    )


def reverse_seed(apps, schema_editor):
    ChartAccount = apps.get_model("finance", "ChartAccount")
    ChartAccount.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("finance", "0001_initial")]

    operations = [migrations.RunPython(seed_chart_account, reverse_seed)]
