from calendar import monthrange
from datetime import date

from django.db import transaction as db_transaction
from rest_framework import serializers

from finance.models import BankAccount, ChartAccount, Transaction
from system.models import SystemSettings
from contracts.models import Contract


def _resolve_defaults():
    """Conta contábil e conta bancária padrão usadas nas cobranças de aluguel.

    Prioriza as configurações do sistema; se não estiverem definidas, usa a
    primeira conta ativa de cada tipo. Se nada existir, o contrato não pode
    ser criado — as cobranças automáticas precisam de um destino contábil.
    """
    settings = SystemSettings.get()

    chart_account = (
        settings.default_rent_chart_account
        or ChartAccount.objects.filter(
            type=ChartAccount.Type.ENTRIES, is_active=True
        )
        .order_by("code")
        .first()
    )
    bank_account = (
        settings.default_bank_account
        or BankAccount.objects.filter(is_active=True).order_by("id").first()
    )

    if chart_account is None or bank_account is None:
        raise serializers.ValidationError(
            "Nenhuma conta contábil de entrada ou conta bancária encontrada. "
            "Cadastre o plano de contas e uma conta bancária (ou defina os "
            "padrões em Configurações) antes de criar contratos."
        )

    return chart_account, bank_account


def _due_date_for(year, month, due_day):
    """Vencimento no mês — se o dia de vencimento não existe no mês
    (ex.: dia 31 em fevereiro), usa o último dia do mês."""
    last_day = monthrange(year, month)[1]
    return date(year, month, min(due_day, last_day))


def _next_month(year, month):
    return (year + 1, 1) if month == 12 else (year, month + 1)


def create_rent_charges(contract, exclude_competence=None):
    """Gera automaticamente as cobranças mensais de aluguel do contrato.

    `exclude_competence`: lista de competências (primeiro dia do mês) que já
    possuem cobrança paga/cancelada — usadas ao sincronizar um contrato
    alterado, para não duplicar histórico.
    """
    charges = []
    chart_account, bank_account = _resolve_defaults()
    exclude = set(exclude_competence or [])

    year, month = contract.start_date.year, contract.start_date.month
    due_date = _due_date_for(year, month, contract.due_day)

    # Se o primeiro vencimento cair em/antes do início, começa no mês seguinte
    if due_date <= contract.start_date:
        year, month = _next_month(year, month)
        due_date = _due_date_for(year, month, contract.due_day)

    while due_date <= contract.end_date:
        if due_date.replace(day=1) not in exclude:
            charges.append(
                Transaction(
                    description=(
                        f"Aluguel - {contract.property.description} - "
                        f"{due_date.strftime('%m/%Y')}"
                    ),
                    status=Transaction.Status.PENDING,
                    amount=contract.monthly_rent,
                    due_date=due_date,
                    payment_date=None,
                    competence_date=due_date.replace(day=1),
                    account=chart_account,
                    bank_account=bank_account,
                    property=contract.property,
                    contract=contract,
                    recurrence=Transaction.Recurrence.MONTHLY,
                )
            )

        year, month = _next_month(year, month)
        due_date = _due_date_for(year, month, contract.due_day)

    Transaction.objects.bulk_create(charges)
    return charges


def sync_rent_charges(contract):
    """Sincroniza as cobranças após alteração no contrato (valores/período).

    Cobranças já pagas ou canceladas são preservadas; as em aberto são
    regeradas a partir dos dados atuais do contrato.
    """
    open_statuses = [Transaction.Status.PENDING, Transaction.Status.OVERDUE]
    kept = list(
        contract.transactions.exclude(status__in=open_statuses).values_list(
            "competence_date", flat=True
        )
    )
    contract.transactions.filter(status__in=open_statuses).delete()
    return create_rent_charges(contract, exclude_competence=kept)


def close_contract(contract):
    """Encerra o contrato antecipadamente e cancela as cobranças em aberto."""
    contract.status = Contract.Status.CANCELLED
    contract.save(update_fields=["status", "updated_at"])
    contract.transactions.filter(
        status__in=[Transaction.Status.PENDING, Transaction.Status.OVERDUE]
    ).update(status=Transaction.Status.CANCELLED)
    return contract


def create_contract_with_transactions(serializer):
    with db_transaction.atomic():
        contract = serializer.save()
        create_rent_charges(contract)
    return contract
