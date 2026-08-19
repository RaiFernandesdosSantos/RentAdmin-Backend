from django.db import models
import tenants.models as tenant_models
import properties.models as property_models


class Contract(models.Model):
    class Status(models.IntegerChoices):
        ACTIVE = 0, "Ativo"
        EXPIRING = 1, "A vencer"
        EXPIRED = 2, "Vencido"
        CANCELLED = 3, "Encerrado"
        RENEWED = 4, "Renovado"

    id = models.AutoField(primary_key=True)
    property = models.ForeignKey(property_models.Property, on_delete=models.CASCADE)
    tenant = models.ForeignKey(
        tenant_models.Tenant, on_delete=models.CASCADE, related_name="contracts"
    )
    guarantor = models.ForeignKey(
        tenant_models.Tenant,
        on_delete=models.CASCADE,
        related_name="guaranteed_contracts",
        null=True,
        blank=True,
    )
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    due_day = models.IntegerField(default=10)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.PositiveIntegerField(choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
