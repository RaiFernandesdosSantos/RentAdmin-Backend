import properties.models as models
from properties.serializers import (
    PropertySerializer,
    PropertyCreateSerializer,
    PropertySoldSerializer,
)
from rest_framework import generics


class PropertyListView(generics.ListAPIView):
    queryset = models.Property.objects.all()
    serializer_class = PropertySerializer


class PropertyRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Property.objects.all()
    serializer_class = PropertySerializer
    lookup_url_kwarg = "id"


class PropertyCreateView(generics.CreateAPIView):
    queryset = models.Property.objects.all()
    serializer_class = PropertyCreateSerializer


class PropertySoldView(generics.UpdateAPIView):
    queryset = models.Property.objects.all()
    serializer_class = PropertySoldSerializer
    lookup_url_kwarg = "id"
