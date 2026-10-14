import contracts.models as models
from contracts.serializers import ContractSerializer, ContractCreateUpdateSerializer
from rest_framework import generics
from rest_framework.response import Response
from contracts.service import (
    create_contract_with_transactions,
    sync_rent_charges,
    close_contract,
)


class ContractListView(generics.ListAPIView):
    serializer_class = ContractSerializer

    def get_queryset(self):
        """Filtros opcionais: ?tenant=&guarantor=&property=&status="""
        qs = models.Contract.objects.select_related(
            "property", "tenant", "guarantor"
        )

        params = self.request.query_params
        tenant = params.get("tenant")
        guarantor = params.get("guarantor")
        property_id = params.get("property")
        status = params.get("status")

        if tenant:
            qs = qs.filter(tenant_id=tenant)
        if guarantor:
            qs = qs.filter(guarantor_id=guarantor)
        if property_id:
            qs = qs.filter(property_id=property_id)
        if status:
            qs = qs.filter(status=status)

        return qs


class ContractRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Contract.objects.select_related("property", "tenant", "guarantor")
    lookup_url_kwarg = "id"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ContractCreateUpdateSerializer
        return ContractSerializer

    def perform_update(self, serializer):
        """Ao alterar valores/período, as cobranças em aberto são
        sincronizadas automaticamente (histórico pago é preservado)."""
        contract = serializer.save()
        sync_rent_charges(contract)


class ContractCreateView(generics.CreateAPIView):
    queryset = models.Contract.objects.all()
    serializer_class = ContractCreateUpdateSerializer

    def perform_create(self, serializer):
        create_contract_with_transactions(serializer)


class ContractCloseView(generics.GenericAPIView):
    """POST /contracts/<id>/close/ — encerra o contrato antecipadamente
    e cancela as cobranças em aberto."""

    queryset = models.Contract.objects.all()
    serializer_class = ContractSerializer
    lookup_url_kwarg = "id"

    def post(self, request, *args, **kwargs):
        contract = close_contract(self.get_object())
        return Response(ContractSerializer(contract).data)


class ContractPdfView(generics.GenericAPIView):
    """GET /contracts/<id>/contract-pdf/ — gera o contrato de locação
    em PDF (módulo Emissão de arquivos)."""

    queryset = models.Contract.objects.select_related(
        "property", "tenant", "guarantor"
    )
    lookup_url_kwarg = "id"

    def get(self, request, *args, **kwargs):
        from django.http import HttpResponse

        from contracts.documents import build_contract_pdf

        contract = self.get_object()
        pdf_bytes = build_contract_pdf(contract)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="contrato-{contract.id}-{contract.tenant.name}.pdf"'
        )
        return response
