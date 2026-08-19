from rest_framework import serializers
import properties.models as models


class PropertyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Property
        fields = [
            "description",
            "property_type",
            "street",
            "number",
            "neighborhood",
            "registration",
            "city",
            "state",
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


class PropertySerializer(serializers.ModelSerializer):
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
            "city",
            "state",
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
        ]


class PropertySoldSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Property
        fields = ["status", "sold_price", "sold_date"]
