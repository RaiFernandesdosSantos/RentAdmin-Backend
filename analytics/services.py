# analytics/services.py
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from properties.models import Property
from contracts.models import Contract
from finance.models import ChartAccount, Transaction


def _money(value):
    """Converte Decimal para string com 2 casas — o contrato de API do
    frontend espera valores monetários como string ("1500.00")."""
    if value is None:
        return None
    return f"{Decimal(value):.2f}"


def get_monthly_revenue(year: int, month: int) -> dict:
    """Receita total do mês e delta vs mês anterior"""
    current = Transaction.objects.filter(
        status=Transaction.Status.PAID,
        competence_date__year=year,
        competence_date__month=month,
        account__type=ChartAccount.Type.ENTRIES,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    # mês anterior
    first_of_month = date(year, month, 1)
    prev = first_of_month - timedelta(days=1)
    previous = Transaction.objects.filter(
        status=Transaction.Status.PAID,
        competence_date__year=prev.year,
        competence_date__month=prev.month,
        account__type=ChartAccount.Type.ENTRIES,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    delta = current - previous
    delta_pct = (delta / previous * 100) if previous > 0 else Decimal("0")

    return {
        "total": _money(current),
        "previous": _money(previous),
        "delta": _money(delta),
        "delta_pct": round(delta_pct, 1),
    }


def get_portfolio_roe() -> dict:
    """ROE médio do portfólio — aluguel anualizado / valor estimado"""
    properties = Property.objects.filter(
        status=Property.Status.RENTED,
        actual_value__gt=0,
    ).prefetch_related("contract_set")

    roe_list = []
    for prop in properties:
        active_contract = (
            prop.contract_set.filter(status=Contract.Status.ACTIVE).first()
        )

        if active_contract and prop.actual_value:
            annual_rent = active_contract.monthly_rent * 12
            roe = (annual_rent / prop.actual_value) * 100
            roe_list.append(
                {
                    "property_id": prop.id,
                    "property_name": prop.description,
                    "property_type": prop.get_property_type_display(),
                    "roe": round(roe, 1),
                    "monthly_rent": _money(active_contract.monthly_rent),
                    "status": "rented",
                }
            )

    # imóveis vagos também aparecem na lista
    vacant = Property.objects.filter(status=Property.Status.AVAILABLE)
    for prop in vacant:
        roe_list.append(
            {
                "property_id": prop.id,
                "property_name": prop.description,
                "property_type": prop.get_property_type_display(),
                "roe": None,
                "monthly_rent": None,
                "status": "vacant",
            }
        )

    avg_roe = (
        sum(p["roe"] for p in roe_list if p["roe"] is not None)
        / len([p for p in roe_list if p["roe"] is not None])
        if any(p["roe"] for p in roe_list)
        else 0
    )

    return {
        "average_roe": round(avg_roe, 1),
        "properties": roe_list,
    }


def get_vacancy() -> dict:
    """Imóveis vagos e percentual do portfólio"""
    total = Property.objects.exclude(status=Property.Status.SOLD).count()
    vacant = Property.objects.filter(status=Property.Status.AVAILABLE).count()
    pct = round((vacant / total * 100), 1) if total > 0 else 0

    return {
        "total_properties": total,
        "vacant_count": vacant,
        "vacant_pct": pct,
    }


def get_expiring_contracts(days: int = 60) -> list:
    """Contratos que vencem nos próximos X dias"""
    today = date.today()
    deadline = today + timedelta(days=days)

    contracts = (
        Contract.objects.filter(
            status__in=[Contract.Status.ACTIVE, Contract.Status.EXPIRING],
            end_date__gte=today,
            end_date__lte=deadline,
        )
        .select_related("tenant", "property")
        .order_by("end_date")
    )

    return [
        {
            "contract_id": c.id,
            "tenant_name": c.tenant.name,
            "property_name": c.property.description,
            "end_date": c.end_date,
            "days_remaining": (c.end_date - today).days,
        }
        for c in contracts
    ]


def get_default_summary(year: int) -> dict:
    """Inadimplência — em aberto no mês, acumulado no ano, taxa"""
    today = date.today()

    # em aberto no mês atual
    overdue_month = Transaction.objects.filter(
        status=Transaction.Status.OVERDUE,
        competence_date__year=today.year,
        competence_date__month=today.month,
        account__type=ChartAccount.Type.ENTRIES,
    )
    overdue_month_total = overdue_month.aggregate(
        total=Sum("amount"), count=Count("id")
    )

    # acumulado no ano
    overdue_year = Transaction.objects.filter(
        status=Transaction.Status.OVERDUE,
        competence_date__year=year,
        account__type=ChartAccount.Type.ENTRIES,
    )
    overdue_year_total = overdue_year.aggregate(total=Sum("amount"), count=Count("id"))

    # taxa — overdue / total esperado no ano
    total_expected = Transaction.objects.filter(
        competence_date__year=year,
        account__type=ChartAccount.Type.ENTRIES,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    overdue_amount = overdue_year_total["total"] or Decimal("0")
    rate = (
        (overdue_amount / total_expected * 100) if total_expected > 0 else Decimal("0")
    )

    return {
        "overdue_this_month": _money(overdue_month_total["total"] or Decimal("0")),
        "overdue_this_month_count": overdue_month_total["count"] or 0,
        "overdue_year_total": _money(overdue_year_total["total"] or Decimal("0")),
        "overdue_year_count": overdue_year_total["count"] or 0,
        "default_rate": round(rate, 1),
    }


def get_monthly_revenue_chart(year: int) -> list:
    """Receita mês a mês dos últimos 12 meses pro gráfico"""
    today = date.today()
    result = []

    first_of_current = date(today.year, today.month, 1)
    for i in range(11, -1, -1):
        ref = first_of_current - relativedelta(months=i)
        total = Transaction.objects.filter(
            status=Transaction.Status.PAID,
            competence_date__year=ref.year,
            competence_date__month=ref.month,
            account__type=ChartAccount.Type.ENTRIES,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        result.append(
            {
                "month": ref.strftime("%b/%y"),
                "year": ref.year,
                "month_number": ref.month,
                "total": _money(total),
            }
        )

    return result


# analytics/services.py


def get_dre(year: int, month: int = None, period: str = "monthly") -> dict:
    """
    DRE — só contas com report_classification = DRE_DFC ou DRE_ONLY
    period: 'monthly' | 'quarterly' | 'annual'
    """
    from finance.models import ChartAccount

    # monta o filtro de período
    filters = Q(
        status=Transaction.Status.PAID,
        account__report_classification__in=[
            ChartAccount.ReportClass.DRE_DFC,
            ChartAccount.ReportClass.DRE_ONLY,
        ],
    )

    if period == "monthly" and month:
        filters &= Q(competence_date__year=year, competence_date__month=month)
        # mês anterior pra comparação
        first = date(year, month, 1)
        prev = first - timedelta(days=1)
        prev_filters = Q(
            status=Transaction.Status.PAID,
            competence_date__year=prev.year,
            competence_date__month=prev.month,
            account__report_classification__in=[
                ChartAccount.ReportClass.DRE_DFC,
                ChartAccount.ReportClass.DRE_ONLY,
            ],
        )
    elif period == "annual":
        filters &= Q(competence_date__year=year)
        prev_filters = Q(
            status=Transaction.Status.PAID,
            competence_date__year=year - 1,
            account__report_classification__in=[
                ChartAccount.ReportClass.DRE_DFC,
                ChartAccount.ReportClass.DRE_ONLY,
            ],
        )
    else:
        prev_filters = None

    # busca contas pai (grupos) do tipo receita e despesa
    revenue_groups = ChartAccount.objects.filter(
        type=ChartAccount.Type.ENTRIES,
        parent__isnull=False,
        parent__parent__isnull=True,  # segundo nível — grupos como "1.1 Aluguel"
        report_classification__in=[
            ChartAccount.ReportClass.DRE_DFC,
            ChartAccount.ReportClass.DRE_ONLY,
        ],
    ).prefetch_related("children")

    expense_groups = ChartAccount.objects.filter(
        type=ChartAccount.Type.EXPENSES,
        parent__isnull=False,
        parent__parent__isnull=True,
        report_classification__in=[
            ChartAccount.ReportClass.DRE_DFC,
            ChartAccount.ReportClass.DRE_ONLY,
        ],
    ).prefetch_related("children")

    def build_group(groups, tx_filters, prev_tx_filters):
        result = []
        grand_total = Decimal("0")
        grand_total_prev = Decimal("0")
        for group in groups:
            children = []
            group_total = Decimal("0")
            group_total_prev = Decimal("0")

            for child in group.children.all():
                current_total = Transaction.objects.filter(
                    tx_filters, account=child
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

                prev_total = (
                    Transaction.objects.filter(
                        prev_tx_filters, account=child
                    ).aggregate(total=Sum("amount"))["total"]
                    or Decimal("0")
                    if prev_tx_filters
                    else Decimal("0")
                )

                # acumulado no ano sempre
                accumulated = Transaction.objects.filter(
                    status=Transaction.Status.PAID,
                    competence_date__year=year,
                    account=child,
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

                group_total += current_total
                group_total_prev += prev_total

                children.append(
                    {
                        "account_id": child.id,
                        "code": child.code,
                        "name": child.name,
                        "current": _money(current_total),
                        "previous": _money(prev_total),
                        "accumulated": _money(accumulated),
                    }
                )

            grand_total += group_total
            grand_total_prev += group_total_prev

            result.append(
                {
                    "group_id": group.id,
                    "code": group.code,
                    "name": group.name,
                    "total": _money(group_total),
                    "total_prev": _money(group_total_prev),
                    "children": children,
                }
            )

        return result, grand_total, grand_total_prev

    revenues, total_revenue, _ = build_group(revenue_groups, filters, prev_filters)
    expenses, total_expenses, _ = build_group(expense_groups, filters, prev_filters)

    net_result = total_revenue - total_expenses
    margin = (
        round((net_result / total_revenue * 100), 1)
        if total_revenue > 0
        else Decimal("0")
    )

    return {
        "period": {"year": year, "month": month, "type": period},
        "revenues": revenues,
        "expenses": expenses,
        "total_revenue": _money(total_revenue),
        "total_expenses": _money(total_expenses),
        "net_result": _money(net_result),
        "margin": float(margin),
    }


def get_dfc(year: int, month: int = None, period: str = "monthly") -> dict:
    """
    DFC — todas as contas (DRE_DFC + DFC_ONLY)
    Inclui seção separada pra contas não-operacionais (DFC_ONLY)
    """
    from finance.models import ChartAccount, BankAccount

    base_filter = Q(
        status=Transaction.Status.PAID,
        account__report_classification__in=[
            ChartAccount.ReportClass.DRE_DFC,
            ChartAccount.ReportClass.DFC_ONLY,
        ],
    )

    if period == "monthly" and month:
        period_filter = Q(competence_date__year=year, competence_date__month=month)
        first = date(year, month, 1)
        prev = first - timedelta(days=1)
        prev_period_filter = Q(
            competence_date__year=prev.year, competence_date__month=prev.month
        )
    elif period == "annual":
        period_filter = Q(competence_date__year=year)
        prev_period_filter = Q(competence_date__year=year - 1)
    else:
        period_filter = Q(competence_date__year=year, competence_date__month=month or 1)
        prev_period_filter = Q()

    def build_dfc_section(account_type, classification_filter):
        groups = ChartAccount.objects.filter(
            type=account_type,
            parent__isnull=False,
            parent__parent__isnull=True,
            report_classification__in=classification_filter,
        ).prefetch_related("children")

        result = []
        section_total = Decimal("0")
        for group in groups:
            children = []
            group_total = Decimal("0")

            grand = Decimal("0")

            for child in group.children.all():
                current = Transaction.objects.filter(
                    base_filter & period_filter, account=child
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

                previous = Transaction.objects.filter(
                    base_filter & prev_period_filter, account=child
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

                accumulated = Transaction.objects.filter(
                    status=Transaction.Status.PAID,
                    competence_date__year=year,
                    account=child,
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

                group_total += current
                grand += current

                children.append(
                    {
                        "account_id": child.id,
                        "code": child.code,
                        "name": child.name,
                        "current": _money(current),
                        "previous": _money(previous),
                        "accumulated": _money(accumulated),
                    }
                )

            section_total += grand

            result.append(
                {
                    "group_id": group.id,
                    "code": group.code,
                    "name": group.name,
                    "total": _money(grand),
                    "children": children,
                }
            )

        return result, section_total

    # entradas operacionais
    inflows, total_inflows = build_dfc_section(
        ChartAccount.Type.ENTRIES,
        [ChartAccount.ReportClass.DRE_DFC],
    )

    # saídas operacionais
    outflows, total_outflows = build_dfc_section(
        ChartAccount.Type.EXPENSES,
        [ChartAccount.ReportClass.DRE_DFC],
    )

    # saídas não-operacionais — só DFC
    non_operational, total_non_op = build_dfc_section(
        ChartAccount.Type.EXPENSES,
        [ChartAccount.ReportClass.DFC_ONLY],
    )

    # saldo inicial — último balance_after antes do período
    from finance.models import BankAccountEntries

    first_day = date(year, month or 1, 1)
    last_entry_before = (
        BankAccountEntries.objects.filter(entry_date__lt=first_day)
        .order_by("-entry_date", "-created_at")
        .first()
    )

    initial_balance = (
        last_entry_before.balance_after if last_entry_before else Decimal("0")
    )

    cash_variation = total_inflows - total_outflows - total_non_op
    final_balance = initial_balance + cash_variation

    return {
        "period": {"year": year, "month": month, "type": period},
        "initial_balance": _money(initial_balance),
        "inflows": inflows,
        "outflows": outflows,
        "non_operational": non_operational,
        "total_inflows": _money(total_inflows),
        "total_outflows": _money(total_outflows),
        "total_non_op": _money(total_non_op),
        "cash_variation": _money(cash_variation),
        "final_balance": _money(final_balance),
    }
