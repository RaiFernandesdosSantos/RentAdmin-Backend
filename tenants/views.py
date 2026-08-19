import tenants.models as models
from tenants.serializers import TenantSerializer, TenantCreateSerializer
from rest_framework import generics


class TenantListView(generics.ListAPIView):
    queryset = models.Tenant.objects.all()
    serializer_class = TenantSerializer


class TenantRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Tenant.objects.all()
    serializer_class = TenantSerializer
    lookup_url_kwarg = "id"


class TenantCreateView(generics.CreateAPIView):
    queryset = models.Tenant.objects.all()
    serializer_class = TenantCreateSerializer
