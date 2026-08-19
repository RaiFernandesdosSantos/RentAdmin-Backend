"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from tenants.views import (
    TenantListView,
    TenantRetrieveUpdateDeleteView,
    TenantCreateView,
)
from properties.views import (
    PropertyListView,
    PropertyRetrieveUpdateDeleteView,
    PropertyCreateView,
)
from finance.views import (
    TransactionListView,
    TransactionRetrieveUpdateDeleteView,
    TransactionCreateView,
)
from contracts.views import (
    ContractListView,
    ContractRetrieveUpdateDeleteView,
    ContractCreateView,
)
from system.views import SystemSettingsView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("tenants/", TenantListView.as_view()),
    path("tenants/<int:id>/", TenantRetrieveUpdateDeleteView.as_view()),
    path("tenants/create/", TenantCreateView.as_view()),
    path("properties/", PropertyListView.as_view()),
    path("properties/<int:id>/", PropertyRetrieveUpdateDeleteView.as_view()),
    path("properties/create/", PropertyCreateView.as_view()),
    path("transactions/", TransactionListView.as_view()),
    path("transactions/<int:id>/", TransactionRetrieveUpdateDeleteView.as_view()),
    path("transactions/create/", TransactionCreateView.as_view()),
    path("contracts/", ContractListView.as_view()),
    path("contracts/<int:id>/", ContractRetrieveUpdateDeleteView.as_view()),
    path("contracts/create/", ContractCreateView.as_view()),
    path("system/", SystemSettingsView.as_view()),
]
