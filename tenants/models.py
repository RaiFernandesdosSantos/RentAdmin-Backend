from django.db import models
from core_app.validators.validate_values import validate_not_blank
from core_app.validators.validate_numbers import validate_positive
from tenants.validators import validate_cpf


class Tenant(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=255,
        validators=[validate_not_blank],
        blank=False,
        null=False,
    )
    cpf = models.CharField(
        max_length=11,
        unique=True,
        validators=[validate_not_blank, validate_cpf],
        blank=False,
        null=False,
    )
    email = models.EmailField(
        unique=True, validators=[validate_not_blank], blank=False, null=False
    )
    phone_number = models.CharField(
        max_length=20, validators=[validate_not_blank], blank=False, null=False
    )
    guarantor = models.BooleanField(default=False)
    profession = models.CharField(
        max_length=100, blank=False, null=False, validators=[validate_not_blank]
    )
    monthly_income = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[validate_positive, validate_not_blank],
        null=False,
        blank=False,
    )
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    street = models.CharField(max_length=200, null=True, blank=True)
    number = models.CharField(max_length=20, null=True, blank=True)
    neighborhood = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
