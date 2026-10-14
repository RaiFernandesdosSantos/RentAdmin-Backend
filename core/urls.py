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
    PropertySoldView,
)
from finance.views import (
    TransactionListView,
    TransactionRetrieveUpdateDeleteView,
    TransactionCreateView,
    BankAccountCreateView,
    BankAccountListView,
    BankAccountRetrieveUpdateDeleteView,
    ChartAccountListView,
    ChartAccountCreateView,
    ChartAccountRetrieveUpdateDeleteView,
    BankAccountEntriesCreateView,
    BankAccountEntriesListView,
    CollectionsOverdueListView,
    CollectionsMarkOverdueView,
    CollectionEmailPreviewView,
    CollectionSendEmailView,
)
from contracts.views import (
    ContractListView,
    ContractRetrieveUpdateDeleteView,
    ContractCreateView,
    ContractCloseView,
    ContractPdfView,
)
from system.views import SystemSettingsView
from analytics.views import (
    PortfolioSummaryView,
    MonthlyRevenueChartView,
    PropertyROEView,
    ExpiringContractsView,
    DefaultSummaryView,
    DREView,
    DFCView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    ## URLS Contracts
    path("contracts/", ContractListView.as_view()),
    path("contracts/<int:id>/", ContractRetrieveUpdateDeleteView.as_view()),
    path("contracts/create/", ContractCreateView.as_view()),
    path("contracts/<int:id>/close/", ContractCloseView.as_view()),
    path("contracts/<int:id>/contract-pdf/", ContractPdfView.as_view()),
    ## ------------------------------------------------------------------------------
    ## URLS Finance
    ## Transactions
    path("finance/transactions/", TransactionListView.as_view()),
    path(
        "finance/transactions/<int:id>/", TransactionRetrieveUpdateDeleteView.as_view()
    ),
    path("finance/transactions/create/", TransactionCreateView.as_view()),
    ## BankAccount
    path("finance/bank_account/", BankAccountListView.as_view()),
    path(
        "finance/bank_account/<int:id>/", BankAccountRetrieveUpdateDeleteView.as_view()
    ),
    path("finance/bank_account/create/", BankAccountCreateView.as_view()),
    ## ChartAccount
    path("finance/chart_account/", ChartAccountListView.as_view()),
    path(
        "finance/chart_account/<int:id>/",
        ChartAccountRetrieveUpdateDeleteView.as_view(),
    ),
    path("finance/chart_account/create/", ChartAccountCreateView.as_view()),
    ## BankAccountEntries
    path("finance/entries/", BankAccountEntriesListView.as_view()),
    path("finance/entries/create/", BankAccountEntriesCreateView.as_view()),
    ## Collections (cobrança de aluguéis)
    path("finance/collections/overdue/", CollectionsOverdueListView.as_view()),
    path("finance/collections/mark-overdue/", CollectionsMarkOverdueView.as_view()),
    path(
        "finance/collections/<int:id>/email-preview/",
        CollectionEmailPreviewView.as_view(),
    ),
    path(
        "finance/collections/<int:id>/send-email/",
        CollectionSendEmailView.as_view(),
    ),
    ## ------------------------------------------------------------------------------
    ## URLS Tenants
    path("tenants/", TenantListView.as_view()),
    path("tenants/<int:id>/", TenantRetrieveUpdateDeleteView.as_view()),
    path("tenants/create/", TenantCreateView.as_view()),
    ## ------------------------------------------------------------------------------
    ## URLS Properties
    path("properties/", PropertyListView.as_view()),
    path("properties/<int:id>/", PropertyRetrieveUpdateDeleteView.as_view()),
    path("properties/create/", PropertyCreateView.as_view()),
    path("properties/<int:id>/sold/", PropertySoldView.as_view()),
    ## ------------------------------------------------------------------------------
    ## URLS Analytics
    path("analytics/summary", PortfolioSummaryView.as_view()),
    path("analytics/summary/", PortfolioSummaryView.as_view()),
    path("analytics/revenue-chart", MonthlyRevenueChartView.as_view()),
    path("analytics/revenue-chart/", MonthlyRevenueChartView.as_view()),
    path("analytics/roe", PropertyROEView.as_view()),
    path("analytics/roe/", PropertyROEView.as_view()),
    path("analytics/expiring", ExpiringContractsView.as_view()),
    path("analytics/expiring/", ExpiringContractsView.as_view()),
    path("analytics/default", DefaultSummaryView.as_view()),
    path("analytics/default/", DefaultSummaryView.as_view()),
    path("analytics/dre/", DREView.as_view()),
    path("analytics/dfc/", DFCView.as_view()),
    ## URLS System
    path("system/", SystemSettingsView.as_view()),
    path("settings/", SystemSettingsView.as_view()),
]
