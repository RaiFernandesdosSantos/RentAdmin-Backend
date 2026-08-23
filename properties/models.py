from django.db import models
from core_app.validators.validate_numbers import (
    validate_positive,
    validate_minimum,
)
from properties.validators import validate_zip


class Property(models.Model):
    class PropertyType(models.IntegerChoices):
        LAND = 0, "Terreno"
        RESIDENCIAL = 1, "Residencial"
        COMERCIAL = 2, "Comercial"

    class Status(models.IntegerChoices):
        AVAILABLE = 0, "Disponivel"
        RENTED = 1, "Alugado"
        MAINTENANCE = 2, "Em Manutencao"
        SOLD = 3, "Vencido"

    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=255, blank=False, null=False)
    property_type = models.PositiveIntegerField(
        choices=PropertyType.choices, default=PropertyType.LAND, blank=False, null=False
    )
    street = models.CharField(max_length=255, blank=False, null=False)
    number = models.PositiveIntegerField(
        blank=False,
        null=False,
    )
    neighborhood = models.CharField(max_length=255, blank=False, null=False)
    registration = models.CharField(max_length=100, blank=False, null=False)
    zip_code = models.CharField(
        max_length=8, validators=[validate_zip], blank=False, null=False
    )
    acquisition_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    acquisition_date = models.DateField(blank=True, null=True)
    actual_value = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )

    ## Futuramente fazer um módulo para expansão de casas

    square_meters = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=False,
        null=False,
    )
    number_of_bedrooms = models.IntegerField(
        blank=True,
        null=True,
    )
    number_of_bathrooms = models.IntegerField(
        blank=True,
        null=True,
    )
    garage_spaces = models.IntegerField(
        blank=True,
        null=True,
    )

    ## -------------------------------------------------------------------------

    status = models.PositiveIntegerField(
        choices=Status.choices, default=Status.AVAILABLE, blank=False, null=False
    )
    sold_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    sold_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.description

    class Meta:
        ordering = ["description"]
