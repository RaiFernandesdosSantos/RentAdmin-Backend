from django.db import models
from contracts.models import Contract
from properties.models import Property


class BankAccount(models.Model):
    id = models.AutoField(primary_key=True)
    bank_name = models.CharField(max_length=100, blank=False, null=False)
    account_number = models.CharField(max_length=20, blank=False, null=False)
    agency_number = models.CharField(max_length=20, blank=False, null=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ChartAccount(models.Model):
    class Type(models.IntegerChoices):
        ENTRIES = 0, "Entradas"
        EXPENSES = 1, "Saídas"

    class ReportClass(models.IntegerChoices):
        DRE_DFC = 0, "DRE e DFC"
        DFC_ONLY = 1, "Apenas DFC"
        DRE_ONLY = 2, "Apenas DRE"

    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=20, blank=False, null=False)
    name = models.CharField(max_length=100, blank=False, null=False)
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="children"
    )
    type = models.PositiveIntegerField(choices=Type.choices, blank=False, null=False)
    report_classification = models.PositiveIntegerField(
        choices=ReportClass.choices, blank=False, null=False
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]


class Transaction(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 0, "Pendente"
        PAID = 1, "Pago"
        OVERDUE = 2, "Em atraso"
        CANCELLED = 3, "Cancelado"

    ##Depois adicionar recorrencia

    class Recurrence(models.IntegerChoices):
        NONE = 0, "Não"
        MONTHLY = 1, "Mensal"
        ANNUAL = 2, "Anual"

    ## -------------------------------------------

    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=200, blank=False, null=False)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        blank=False,
        null=False,
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=False, null=False
    )
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    competence_date = models.DateField()
    account = models.ForeignKey(
        ChartAccount,
        on_delete=models.PROTECT,
        related_name="transactions",
        blank=False,
        null=False,
    )
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="transactions",
        blank=False,
        null=False,
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    recurrence = models.CharField(
        max_length=10,
        choices=Recurrence.choices,
        default=Recurrence.NONE,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class BankAccountEntries(models.Model):
    id = models.AutoField(primary_key=True)
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="entries",
        blank=False,
        null=False,
    )
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name="entries",
        blank=True,
        null=True,
    )
    balance_before = models.DecimalField(
        max_digits=12, decimal_places=2, blank=False, null=False
    )
    balance_after = models.DecimalField(
        max_digits=12, decimal_places=2, blank=False, null=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
