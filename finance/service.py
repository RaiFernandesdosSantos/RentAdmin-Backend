from django.db import transaction as db_transaction
from django.utils import timezone
from datetime import datetime, time
from decimal import Decimal

from finance.models import BankAccountEntries, ChartAccount, Transaction


def create_initial_bank_entry(bank_account, initial_balance):
    BankAccountEntries.objects.create(
        bank_account=bank_account,
        transaction=None,
        balance_before=Decimal("0.00"),
        balance_after=initial_balance,
        entry_date=timezone.now(),
    )


def get_current_balance(bank_account):
    ## Saldo corrente pela ORDEM DE INSERÇÃO (created_at), não pela data do
    ## movimento: pagamentos retroativos (ex.: aluguel do mês passado baixado
    ## hoje) devem entrar no saldo atual mesmo com data antiga.
    last_entry = bank_account.entries.order_by("-created_at", "-id").first()
    return last_entry.balance_after if last_entry else Decimal("0.00")


def _entry_datetime(payment_date):
    """Data de pagamento (date) -> datetime com timezone para o extrato."""
    if payment_date:
        return timezone.make_aware(datetime.combine(payment_date, time.min))
    return timezone.now()


def sync_entry_for_transaction(transaction):
    """Cria/remove a entrada bancária conforme o estado da transação.

    - PAGA: cria a entrada (se ainda não existir) movimentando o saldo da conta.
    - Não paga (PENDENTE/EM ATRASO/CANCELADA): remove a entrada (se existir),
      pois o saldo só deve mudar quando o dinheiro efetivamente entra/sai.
    """
    entry = transaction.entries.first()

    if transaction.status == Transaction.Status.PAID:
        if entry:
            return entry

        balance_before = get_current_balance(transaction.bank_account)

        if transaction.account.type == ChartAccount.Type.ENTRIES:
            balance_after = balance_before + transaction.amount
        else:
            balance_after = balance_before - transaction.amount

        return BankAccountEntries.objects.create(
            bank_account=transaction.bank_account,
            transaction=transaction,
            balance_before=balance_before,
            balance_after=balance_after,
            entry_date=_entry_datetime(transaction.payment_date),
        )

    if entry:
        entry.delete()
    return None


def create_transaction_with_entry(serializer):
    with db_transaction.atomic():
        transaction = serializer.save()
        sync_entry_for_transaction(transaction)
    return transaction


def update_transaction_with_entry(serializer):
    with db_transaction.atomic():
        transaction = serializer.save()
        sync_entry_for_transaction(transaction)
    return transaction
