from django.db import transaction as db_transaction
from dateutil.relativedelta import relativedelta
from finance.models import Transaction

## from system.models import SystemSettings


def create_rent_charges(contract):
    transaction = []
    due_date = contract.start_date.replace(day=contract.due_day)

    chart_account = 1
    bank_account = 1

    if due_date <= contract.start_date:
        due_date += relativedelta(month=1)

    while due_date <= contract.end_date:
        transaction.append(
            Transaction.objects.create(
                desciption=(
                    f" Aluguel - {contract.property.name} - "
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

        due_date += relativedelta(month=1)

    Transaction.objects.bulk_create(transaction)


def create_contract_with_transactions(serializer):
    with db_transaction.atomic():
        contract = serializer.save()
        create_rent_charges(contract)
    return contract
