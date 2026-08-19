from rest_framework import serializers
from system.models import SystemSettings
from finance.models import BankAccount, ChartAccount


class SystemSettingsSerializer(serializers.ModelSerializer):
    default_bank_account = serializers.PrimaryKeyRelatedField(
        queryset=BankAccount.objects.all(), required=False, allow_null=True
    )
    default_rent_chart_account = serializers.PrimaryKeyRelatedField(
        queryset=ChartAccount.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = SystemSettings
        fields = "__all__"
