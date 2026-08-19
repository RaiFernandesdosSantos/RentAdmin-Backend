from properties.models import Property
from tenants.models import Tenant
from rest_framework import serializers
import contracts.models as models
from tenants.serializers import TenantSerializer
from properties.serializers import PropertySerializer


class ContractValidationMixin:
    def validate_monthly_rent(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Valor do Aluguel deve ser maior que zero."
            )
        return value

    def validate_security_deposit(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Caução deve ser maior que zero ou nula.")
        return value


class ContractCreateUpdateSerializer(
    ContractValidationMixin, serializers.ModelSerializer
):
    property = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all())
    tenant = serializers.PrimaryKeyRelatedField(queryset=Tenant.objects.all())
    guarantor = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = models.Contract
        fields = (
            "property",
            "tenant",
            "guarantor",
            "monthly_rent",
            "security_deposit",
            "due_day",
            "start_date",
            "end_date",
        )


class ContractSerializer(ContractValidationMixin, serializers.ModelSerializer):
    property = PropertySerializer(read_only=True)
    tenant = TenantSerializer(read_only=True)
    guarantor = TenantSerializer(read_only=True)

    class Meta:
        model = models.Contract
        fields = (
            "id",
            "property",
            "tenant",
            "guarantor",
            "monthly_rent",
            "security_deposit",
            "due_day",
            "start_date",
            "end_date",
            "status",
        )
