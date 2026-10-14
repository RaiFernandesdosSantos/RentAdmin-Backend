import finance.models as models
from finance.serializers import (
    TransactionSerializer,
    TransactionCreateSerializer,
    BankAccountSerializer,
    BankAccountCreateSerializer,
    ChartAccountSerializer,
    ChartAccountCreateSerializer,
    BankAccountEntriesSerializer,
    BankAccountEntriesCreateSerializer,
)
from rest_framework import generics
from rest_framework.response import Response
from finance.service import (
    create_initial_bank_entry,
    create_transaction_with_entry,
    update_transaction_with_entry,
)
from finance import collections
from decimal import Decimal

## ---------------------------------------------------------------------------------------------------
## ---------------------------------------------------------------------------------------------------
## ---------------------------------------------------------------------------------------------------
## BankAccount Views


class BankAccountCreateView(generics.CreateAPIView):
    serializer_class = BankAccountCreateSerializer

    ## Cria conta bancaria com transacao incial

    def perform_create(self, serializer):
        bank_account = serializer.save()
        initial_balance = Decimal(self.request.data.get("initial_balance", "0"))
        create_initial_bank_entry(bank_account, initial_balance)


class BankAccountRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    lookup_url_kwarg = "id"


class BankAccountListView(generics.ListAPIView):
    queryset = models.BankAccount.objects.all()
    serializer_class = BankAccountSerializer


## ---------------------------------------------------------------------------------------------------
## ---------------------------------------------------------------------------------------------------
## ---------------------------------------------------------------------------------------------------
## ChartAccount Views


class ChartAccountListView(generics.ListAPIView):
    queryset = models.ChartAccount.objects.all()
    serializer_class = ChartAccountSerializer


class ChartAccountRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.ChartAccount.objects.all()
    serializer_class = ChartAccountSerializer
    lookup_url_kwarg = "id"


class ChartAccountCreateView(generics.CreateAPIView):
    queryset = models.ChartAccount.objects.all()
    serializer_class = ChartAccountCreateSerializer


## ---------------------------------------------------------------------------------------------------
## ---------------------------------------------------------------------------------------------------
## ---------------------------------------------------------------------------------------------------
## Transactions Views


class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        """Filtros opcionais: ?account_type=ENTRIES|EXPENSES&status=PENDING
        &year=&month=&property=&contract="""
        qs = models.Transaction.objects.select_related(
            "account",
            "bank_account",
            "property",
            "contract__tenant",
        )

        params = self.request.query_params
        account_type = params.get("account_type")
        status = params.get("status")
        year = params.get("year")
        month = params.get("month")
        property_id = params.get("property")
        contract_id = params.get("contract")

        if account_type:
            qs = qs.filter(account__type=account_type)
        if status:
            qs = qs.filter(status=status)
        if year:
            qs = qs.filter(competence_date__year=year)
        if month:
            qs = qs.filter(competence_date__month=month)
        if property_id:
            qs = qs.filter(property_id=property_id)
        if contract_id:
            qs = qs.filter(contract_id=contract_id)

        return qs


class TransactionRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Transaction.objects.select_related(
        "account", "bank_account", "property", "contract__tenant"
    )
    serializer_class = TransactionSerializer
    lookup_url_kwarg = "id"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return TransactionCreateSerializer
        return TransactionSerializer

    def perform_update(self, serializer):
        """Ao marcar como PAGO, cria automaticamente a entrada bancária
        (saldo da conta atualizado); ao reabrir, remove a entrada."""
        update_transaction_with_entry(serializer)


class TransactionCreateView(generics.CreateAPIView):
    serializer_class = TransactionCreateSerializer

    def perform_create(self, serializer):
        create_transaction_with_entry(serializer)


## ---------------------------------------------------------------------------------------------------
## ---------------------------------------------------------------------------------------------------
## ---------------------------------------------------------------------------------------------------
## BankAccountEntries Views


class BankAccountEntriesListView(generics.ListAPIView):
    serializer_class = BankAccountEntriesSerializer

    def get_queryset(self):
        qs = models.BankAccountEntries.objects.select_related(
            "transaction", "transaction__account"
        ).order_by("-entry_date", "-created_at")

        bank_account = self.request.query_params.get("bank_account")
        year = self.request.query_params.get("year")
        month = self.request.query_params.get("month")

        if bank_account:
            qs = qs.filter(bank_account=bank_account)
        if year:
            qs = qs.filter(entry_date__year=year)
        if month:
            qs = qs.filter(entry_date__month=month)

        return qs


class BankAccountEntriesCreateView(generics.CreateAPIView):
    serializer_class = BankAccountEntriesCreateSerializer


## ---------------------------------------------------------------------------------------------------
## ---------------------------------------------------------------------------------------------------
## ---------------------------------------------------------------------------------------------------
## Collections (cobrança de aluguéis) Views


class CollectionsOverdueListView(generics.GenericAPIView):
    """GET /finance/collections/overdue/ — cobranças em atraso, com dados
    do inquilino para disparo de e-mails de cobrança."""

    def get(self, request, *args, **kwargs):
        charges = collections.get_overdue_charges()
        total = sum(Decimal(str(c["amount"])) for c in charges)
        return Response(
            {
                "count": len(charges),
                "total_amount": f"{total:.2f}",
                "charges": charges,
            }
        )


class CollectionsMarkOverdueView(generics.GenericAPIView):
    """POST /finance/collections/mark-overdue/ — marca como EM ATRASO as
    cobranças pendentes cujo vencimento já passou."""

    def post(self, request, *args, **kwargs):
        count = collections.mark_overdue_transactions()
        return Response({"marked_overdue": count})


class _CollectionChargeMixin:
    queryset = models.Transaction.objects.select_related(
        "contract__tenant", "contract__property", "property", "account"
    )
    lookup_url_kwarg = "id"


class CollectionEmailPreviewView(_CollectionChargeMixin, generics.GenericAPIView):
    """GET /finance/collections/<id>/email-preview/ — e-mail que será
    enviado para a cobrança, sem enviar."""

    def get(self, request, *args, **kwargs):
        charge = self.get_object()
        email = collections.build_collection_email(charge)
        return Response(email)


class CollectionSendEmailView(_CollectionChargeMixin, generics.GenericAPIView):
    """POST /finance/collections/<id>/send-email/ — envia o e-mail de
    cobrança ao inquilino."""

    def post(self, request, *args, **kwargs):
        charge = self.get_object()
        try:
            result = collections.send_collection_email(charge)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(result)
