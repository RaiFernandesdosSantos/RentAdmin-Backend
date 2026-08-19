from rest_framework import serializers
import finance.models as models
from properties import models as prop, serializers as prop_ser
from contracts import models as contra, serializers as contra_ser


class BankAccountEntriesCreateSerializer:
    bank_account = serializers.PrimaryKeyRelatedField(
        queryset=models.BankAccount.objects.all()
    )
    transactio = serializers.PrimaryKeyRelatedField(
        queryset=models.Transaction.objects.all()
    )

    class Meta:
        model = models.BankAccountEntries
        fields = [
            "bank_account",
            "transaction",
            "balance_before",
            "balance_after",
            "entry_date",
        ]


class BankAccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BankAccount
        fields = ["bank_name", "account_number", "agency_number"]


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BankAccount
        fields = ["id", "bank_name", "account_number", "agency_number", "is_active"]


class ChartAccountCreateSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=models.ChartAccount.objects.all()
    )

    class Meta:
        model = models.ChartAccount
        fields = ["code", "name", "parent", "type", "report_classification"]


class ChartAccountChildrenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ChartAccount
        fields = ["id", "code", "name", "type", "report_classification", "is_active"]


class ChartAccountSerializer(serializers.ModelSerializer):
    parent = ChartAccountChildrenSerializer(read_only=True)

    class Meta:
        model = models.ChartAccount
        fields = [
            "id",
            "code",
            "name",
            "parent",
            "type",
            "report_classification",
            "is_active",
        ]


class TransactionCreateSerializer(serializers.ModelSerializer):
    account = serializers.PrimaryKeyRelatedField(
        queryset=models.ChartAccount.objects.all()
    )
    bank_account = serializers.PrimaryKeyRelatedField(
        queryset=models.BankAccount.objects.all()
    )
    property = serializers.PrimaryKeyRelatedField(
        queryset=prop.Property.objects.all(), required=False, allow_null=True
    )
    contract = serializers.PrimaryKeyRelatedField(
        queryset=contra.Contract.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = models.Transaction
        fields = [
            "description",
            "status",
            "amount",
            "due_date",
            "payment_date",
            "competence_date",
            "account",
            "bank_account",
            "property",
            "contract",
            "recurrence",
        ]


class TransactionSerializer(serializers.ModelSerializer):
    account = ChartAccountSerializer(read_only=True)
    bank_account = BankAccountSerializer(read_only=True)
    property = prop_ser.PropertySerializer(read_only=True)
    contract = contra_ser.ContractSerializer(read_only=True)

    class Meta:
        model = models.Transaction
        fields = [
            "id",
            "description",
            "status",
            "amount",
            "due_date",
            "payment_date",
            "competence_date",
            "account",
            "bank_account",
            "property",
            "contract",
            "recurrence",
        ]


class BankAccountEntriesSerializer:
    bank_account = BankAccountSerializer(read_only=True)

    class Meta:
        model = models.BankAccountEntries
        fields = [
            "id",
            "bank_account",
            "transaction",
            "balance_before",
            "balance_after",
        ]
