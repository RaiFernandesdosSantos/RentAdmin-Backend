# analytics/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from analytics import services


def _int_param(request, name, default):
    """Parâmetro inteiro tolerante: ausente ou vazio usa o padrão."""
    raw = request.query_params.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class PortfolioSummaryView(APIView):
    """GET /analytics/summary/?year=2025&month=1"""

    def get(self, request):
        today = timezone.now().date()
        year = _int_param(request, "year", today.year)
        month = _int_param(request, "month", today.month)
        days = _int_param(request, "days", 60)

        return Response(
            {
                "revenue": services.get_monthly_revenue(year, month),
                "roe": services.get_portfolio_roe(),
                "vacancy": services.get_vacancy(),
                "expiring_contracts": services.get_expiring_contracts(days),
                "default": services.get_default_summary(year),
            }
        )


class MonthlyRevenueChartView(APIView):
    """GET /analytics/revenue-chart/?year=2025"""

    def get(self, request):
        year = _int_param(request, "year", timezone.now().year)
        return Response(services.get_monthly_revenue_chart(year))


class PropertyROEView(APIView):
    """GET /analytics/roe/"""

    def get(self, request):
        return Response(services.get_portfolio_roe())


class ExpiringContractsView(APIView):
    """GET /analytics/expiring/?days=60"""

    def get(self, request):
        days = _int_param(request, "days", 60)
        return Response(services.get_expiring_contracts(days))


class DefaultSummaryView(APIView):
    """GET /analytics/default/?year=2025"""

    def get(self, request):
        year = _int_param(request, "year", timezone.now().year)
        return Response(services.get_default_summary(year))


class DREView(APIView):
    """
    GET /analytics/dre/?year=2025&month=1&period=monthly
    period: monthly | annual
    """

    def get(self, request):
        today = timezone.now().date()
        year = _int_param(request, "year", today.year)
        month = _int_param(request, "month", today.month)
        period = request.query_params.get("period", "monthly")

        return Response(services.get_dre(year, month, period))


class DFCView(APIView):
    """
    GET /analytics/dfc/?year=2025&month=1&period=monthly
    period: monthly | annual
    """

    def get(self, request):
        today = timezone.now().date()
        year = _int_param(request, "year", today.year)
        month = _int_param(request, "month", today.month)
        period = request.query_params.get("period", "monthly")

        return Response(services.get_dfc(year, month, period))
