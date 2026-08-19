from rest_framework import generics
from system.serializers import SystemSettingsSerializer
from system.models import SystemSettings


class SystemSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = SystemSettingsSerializer

    def get_object(self):
        return SystemSettings.get()
