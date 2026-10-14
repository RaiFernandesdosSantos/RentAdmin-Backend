import re

from rest_framework import serializers
import properties.models as models


class ZipNormalizationMixin:
    def validate_zip_code(self, value):
        """Aceita CEP com ou sem máscara e grava apenas os 8 dígitos."""
        if value is None:
            return value
        digits = re.sub(r"\D", "", value)
        if len(digits) != 8:
            raise serializers.ValidationError(
                "O CEP deve conter exatamente 8 dígitos numéricos."
            )
        return digits


## Campo declarado (e não herdado de mixin) para o DRF respeitar o
## max_length ampliado — o CEP pode chegar com máscara (12.345-678).
ZIP_FIELD = serializers.CharField(max_length=16)


class PropertyCreateSerializer(ZipNormalizationMixin, serializers.ModelSerializer):
    zip_code = ZIP_FIELD

    class Meta:
        model = models.Property
        fields = [
            "id",
            "description",
            "property_type",
            "street",
            "number",
            "neighborhood",
            "registration",
            "zip_code",
            "acquisition_price",
            "acquisition_date",
            "actual_value",
            "square_meters",
            "number_of_bedrooms",
            "number_of_bathrooms",
            "garage_spaces",
            "status",
        ]


class PropertySerializer(ZipNormalizationMixin, serializers.ModelSerializer):
    zip_code = ZIP_FIELD

    class Meta:
        model = models.Property
        fields = [
            "id",
            "description",
            "property_type",
            "street",
            "number",
            "neighborhood",
            "registration",
            "zip_code",
            "acquisition_price",
            "acquisition_date",
            "actual_value",
            "square_meters",
            "number_of_bedrooms",
            "number_of_bathrooms",
            "garage_spaces",
            "status",
            "sold_price",
            "sold_date",
            "created_at",
            "updated_at",
        ]


class PropertySoldSerializer(serializers.ModelSerializer):
    """Usado no endpoint de venda (PATCH /properties/<id>/sold/)."""

    class Meta:
        model = models.Property
        fields = ["status", "sold_price", "sold_date"]
        read_only_fields = ["status"]

    def validate(self, attrs):
        sold_price = attrs.get("sold_price")
        sold_date = attrs.get("sold_date")
        if sold_price is None or sold_date is None:
            raise serializers.ValidationError(
                "Informe o preço e a data de venda para registrar a venda."
            )
        attrs["status"] = models.Property.Status.SOLD
        return attrs
