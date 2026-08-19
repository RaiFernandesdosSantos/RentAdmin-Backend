import contracts.models as models
from contracts.serializers import ContractSerializer, ContractCreateUpdateSerializer
from rest_framework import generics
from contracts.service import create_contract_with_transactions


class ContractListView(generics.ListAPIView):
    queryset = models.Contract.objects.all()
    serializer_class = ContractSerializer


class ContractRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Contract.objects.all()
    lookup_url_kwarg = "id"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ContractCreateUpdateSerializer
        return ContractSerializer


class ContractCreateView(generics.CreateAPIView):
    queryset = models.Contract.objects.all()
    serializer_class = ContractCreateUpdateSerializer

    def perform_create(self, serializer):
        create_contract_with_transactions(serializer)
