import finance.models as models
from finance.serializers import (
    TransactionSerializer,
    TransactionCreateSerializer,
    BankAccountSerializer,
    BankAccountCreateSerializer,
    ChartAccountSerializer,
    ChartAccountCreateSerializer,
    BankAccountEntriesSerializer,
)
from rest_framework import generics
from finance.service import create_initial_bank_entry, create_transaction_with_entry
from decimal import Decimal


class BankAccountCreateView(generics.CreateAPIView):
    serializer_class = BankAccountCreateSerializer

    def perform_create(self, serializer):
        bank_account = serializer.save()
        initial_balance = Decimal(self.request.data.get("initial_balance", "0"))
        create_initial_bank_entry(bank_account, initial_balance)


class BankAccountEntriesListView(generics.ListAPIView):
    queryset = models.BankAccountEntries.objects.all()
    serializer_class = BankAccountEntriesSerializer


class ChartAccountListView(generics.ListAPIView):
    queryset = models.ChartAccount.objects.all()
    serializer_class = ChartAccountSerializer


class ChartAccountRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.ChartAccount.objects.all()
    serializer_class = ChartAccountSerializer
    lookup_url_kwarg = "id"


class CharAccountCreateView(generics.CreateAPIView):
    queryset = models.ChartAccount.objects.all()
    serializer_class = ChartAccountCreateSerializer


class BankAccountListView(generics.ListAPIView):
    queryset = models.BankAccount.objects.all()
    serializer_class = BankAccountSerializer


class TransactionListView(generics.ListAPIView):
    queryset = models.Transaction.objects.all()
    serializer_class = TransactionSerializer


class TransactionRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Transaction.objects.all()
    serializer_class = TransactionSerializer
    lookup_url_kwarg = "id"


class TransactionCreateView(generics.CreateAPIView):
    serializer_class = TransactionCreateSerializer

    def perform_create(self, serializer):
        create_transaction_with_entry(serializer)
