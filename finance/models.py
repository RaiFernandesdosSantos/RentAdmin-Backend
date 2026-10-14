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
    ## Valores em string — o contrato de API do frontend espera
    ## "ENTRIES" | "EXPENSES" e "DRE_DFC" | "DFC_ONLY" | "DRE_ONLY"

    class Type(models.TextChoices):
        ENTRIES = "ENTRIES", "Entradas"
        EXPENSES = "EXPENSES", "Saídas"

    class ReportClass(models.TextChoices):
        DRE_DFC = "DRE_DFC", "DRE e DFC"
        DFC_ONLY = "DFC_ONLY", "Apenas DFC"
        DRE_ONLY = "DRE_ONLY", "Apenas DRE"

    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=20, blank=False, null=False)
    name = models.CharField(max_length=100, blank=False, null=False)
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="children"
    )
    type = models.CharField(
        max_length=10,
        choices=Type.choices,
        blank=False,
        null=False,
    )
    report_classification = models.CharField(
        max_length=10,
        choices=ReportClass.choices,
        blank=False,
        null=False,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]


class Transaction(models.Model):
    ## Valores em string — o contrato de API do frontend espera
    ## "PENDING" | "PAID" | "OVERDUE" | "CANCELLED" e "NONE" | "MONTHLY" | "ANNUAL"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        PAID = "PAID", "Pago"
        OVERDUE = "OVERDUE", "Em atraso"
        CANCELLED = "CANCELLED", "Cancelado"

    class Recurrence(models.TextChoices):
        NONE = "NONE", "Não"
        MONTHLY = "MONTHLY", "Mensal"
        ANNUAL = "ANNUAL", "Anual"

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

    def __str__(self):
        return self.description

    class Meta:
        ordering = ["-due_date"]


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
    ## Data em que o movimento aconteceu na conta (ex.: data de pagamento)
    ## — usada pelo extrato e pelo cálculo de saldo inicial do DFC
    entry_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        label = self.transaction.description if self.transaction else "Saldo inicial"
        return f"{self.bank_account} · {label}"
