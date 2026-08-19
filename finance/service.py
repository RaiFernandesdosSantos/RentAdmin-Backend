from django.db import transaction as db_transaction
from finance.models import BankAccountEntries, ChartAccount
from datetime import datetime


def create_initial_bank_entry(bank_account, initial_balance):
    BankAccountEntries.objects.create(
        bank_account=bank_account,
        transaction=None,
        balance_before=0,
        balance_after=initial_balance,
        entry_date=datetime.now(),
    )


def get_current_balance(bank_account):
    last_entry = bank_account.entries.order_by("-created_at").first()
    return last_entry.balance_after


def create_transaction_with_entry(serializer):
    with db_transaction.atomic():
        # 1. salva a transação e já tem o ID
        transaction = serializer.save()

        # 2. busca o saldo atual da conta
        balance_before = get_current_balance(transaction.bank_account)

        # 3. calcula o novo saldo baseado no plano de contas
        chart_account = transaction.chart_account
        if chart_account.type == ChartAccount.Type.ENTRIES:
            balance_after = balance_before + transaction.amount
        else:
            balance_after = balance_before - transaction.amount

        # 4. cria a entrada ligada à transação que acabou de ser criada
        BankAccountEntries.objects.create(
            bank_account=transaction.bank_account,
            transaction=transaction,
            balance_before=balance_before,
            balance_after=balance_after,
            entry_date=transaction.payment_date,
        )
