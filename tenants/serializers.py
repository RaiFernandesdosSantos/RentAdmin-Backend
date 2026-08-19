from rest_framework import serializers
import tenants.models as models


class TenantCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tenant
        fields = (
            "name",
            "cpf",
            "email",
            "phone_number",
            "guarantor",
            "profession",
            "monthly_income",
            "zip_code",
            "street",
            "number",
            "neighborhood",
        )


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tenant
        fields = (
            "id",
            "name",
            "cpf",
            "email",
            "phone_number",
            "guarantor",
            "profession",
            "monthly_income",
            "zip_code",
            "street",
            "number",
            "neighborhood",
            "is_active",
        )
