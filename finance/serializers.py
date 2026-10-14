from rest_framework import serializers
import finance.models as models
from properties import models as prop, serializers as prop_ser
from contracts import models as contra, serializers as contra_ser
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal


class BankAccountEntriesSerializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()
    chart_account = serializers.SerializerMethodField()
    entry_type = serializers.SerializerMethodField()

    class Meta:
        model = models.BankAccountEntries
        fields = [
            "id",
            "bank_account",
            "transaction",
            "balance_before",
            "balance_after",
            "entry_date",
            "created_at",
            "description",
            "chart_account",
            "entry_type",
        ]

    def get_description(self, obj):
        return obj.transaction.description if obj.transaction else "Saldo inicial"

    def get_chart_account(self, obj):
        if obj.transaction and obj.transaction.account:
            return f"{obj.transaction.account.code} · {obj.transaction.account.name}"
        return "—"

    def get_entry_type(self, obj):
        # determina se foi entrada ou saída comparando saldos
        if obj.balance_after > obj.balance_before:
            return "CREDIT"
        return "DEBIT"


class BankAccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BankAccount
        fields = ["id", "bank_name", "account_number", "agency_number"]


class BankAccountSerializer(serializers.ModelSerializer):
    current_balance = serializers.SerializerMethodField()
    monthly_inflows = serializers.SerializerMethodField()
    monthly_outflows = serializers.SerializerMethodField()
    last_movement = serializers.SerializerMethodField()

    class Meta:
        model = models.BankAccount
        fields = (
            "id",
            "bank_name",
            "account_number",
            "agency_number",
            "is_active",
            "created_at",
            "updated_at",
            "current_balance",
            "monthly_inflows",
            "monthly_outflows",
            "last_movement",
        )

    ## Valores monetários SEMPRE como string, conforme o frontend espera

    def get_current_balance(self, obj):
        ## mesma regra do service: ordem de inserção (suporta pagamentos retroativos)
        last = obj.entries.order_by("-created_at", "-id").first()
        return f"{last.balance_after:.2f}" if last else "0.00"

    def get_monthly_inflows(self, obj):
        today = timezone.now().date()
        total = (
            obj.transactions.filter(
                status=models.Transaction.Status.PAID,
                account__type=models.ChartAccount.Type.ENTRIES,
                payment_date__year=today.year,
                payment_date__month=today.month,
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        return f"{total:.2f}"

    def get_monthly_outflows(self, obj):
        today = timezone.now().date()
        total = (
            obj.transactions.filter(
                status=models.Transaction.Status.PAID,
                account__type=models.ChartAccount.Type.EXPENSES,
                payment_date__year=today.year,
                payment_date__month=today.month,
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        return f"{total:.2f}"

    def get_last_movement(self, obj):
        last = obj.entries.order_by("-entry_date", "-created_at").first()
        if not last:
            return None
        return last.entry_date


class ChartAccountCreateSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=models.ChartAccount.objects.all(), required=False, allow_null=True
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


class BankAccountEntriesCreateSerializer(serializers.ModelSerializer):
    bank_account = serializers.PrimaryKeyRelatedField(
        queryset=models.BankAccount.objects.all()
    )
    transaction = serializers.PrimaryKeyRelatedField(
        queryset=models.Transaction.objects.all(), required=False, allow_null=True
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
