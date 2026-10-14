from decimal import Decimal

from django.db import models


class SystemSettings(models.Model):
    ## Dados do locador (usados no contrato em PDF e nos e-mails de cobrança)
    owner_name = models.CharField(max_length=255, blank=True, default="")
    owner_cpf = models.CharField(max_length=14, blank=True, default="")
    owner_phone = models.CharField(max_length=20, blank=True, default="")
    owner_email = models.EmailField(blank=True, default="")

    ## Formatação e exercício fiscal
    date_format = models.CharField(max_length=10, default="DD/MM/YYYY")
    fiscal_year_start = models.PositiveIntegerField(default=1)

    ## Padrões contratuais e financeiros
    default_adjustment_index = models.CharField(max_length=10, default="IGPM")
    default_due_day = models.PositiveIntegerField(default=10)
    contract_alert_days = models.IntegerField(default=60)
    default_late_fee = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    default_interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    default_bank_account = models.ForeignKey(
        "finance.BankAccount",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_rent",
    )
    default_rent_chart_account = models.ForeignKey(
        "finance.ChartAccount",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_rent",
    )
    notify_expiring_contracts = models.BooleanField(default=True)
    notify_overdue_charges = models.BooleanField(default=True)
    notify_vacant_properties = models.BooleanField(default=True)
    notify_upcoming_expenses = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    class Meta:
        verbose_name = "Configurações do sistema"
