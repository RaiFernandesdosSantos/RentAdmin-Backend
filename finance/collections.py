"""E-mails de cobrança — módulo de cobrança de aluguéis em atraso.

Funções:
- `mark_overdue_transactions()`: marca como EM ATRASO as cobranças
  pendentes cujo vencimento já passou (roda a qualquer momento).
- `get_overdue_charges()`: lista as cobranças em atraso com os dados do
  inquilino para a tela de cobranças.
- `build_collection_email()`: monta o e-mail (assunto + corpo) de uma
  cobrança, pronto para envio ou pré-visualização.
- `send_collection_email()`: envia o e-mail usando a configuração SMTP
  das variáveis de ambiente (em dev usa o backend de console).
"""
from datetime import date

from django.conf import settings as django_settings
from django.core.mail import EmailMultiAlternatives

from finance.models import ChartAccount, Transaction
from system.models import SystemSettings


def mark_overdue_transactions(reference_date=None):
    """Pendente com vencimento passado -> EM ATRASO. Retorna a quantidade."""
    reference = reference_date or date.today()
    open_charges = Transaction.objects.filter(
        status=Transaction.Status.PENDING, due_date__lt=reference
    )
    count = open_charges.update(status=Transaction.Status.OVERDUE)
    return count


def get_overdue_charges():
    """Cobranças de aluguel em atraso, com inquilino e imóvel para cobrança."""
    mark_overdue_transactions()

    charges = (
        Transaction.objects.filter(
            status=Transaction.Status.OVERDUE,
            account__type=ChartAccount.Type.ENTRIES,
            contract__isnull=False,
        )
        .select_related("contract__tenant", "contract__property", "account")
        .order_by("due_date")
    )

    result = []
    for charge in charges:
        tenant = charge.contract.tenant if charge.contract else None
        prop = charge.property
        days_late = (date.today() - charge.due_date).days
        result.append(
            {
                "transaction_id": charge.id,
                "description": charge.description,
                "amount": str(charge.amount),
                "due_date": charge.due_date,
                "competence_date": charge.competence_date,
                "days_late": days_late,
                "tenant_id": tenant.id if tenant else None,
                "tenant_name": tenant.name if tenant else None,
                "tenant_email": tenant.email if tenant else None,
                "tenant_phone": tenant.phone_number if tenant else None,
                "property_id": prop.id if prop else None,
                "property_description": prop.description if prop else None,
                "contract_id": charge.contract_id,
            }
        )
    return result


def _brl(value):
    try:
        text = f"{value:,.2f}"
    except (TypeError, ValueError):
        return "—"
    return "R$ " + text.replace(",", "X").replace(".", ",").replace("X", ".")


def _brdate(value):
    if not value:
        return "—"
    return value.strftime("%d/%m/%Y")


def build_collection_email(charge):
    """Monta assunto e corpo (texto) do e-mail de cobrança de uma cobrança."""
    system = SystemSettings.get()
    tenant = charge.contract.tenant if charge.contract else None
    prop = charge.property
    tenant_name = tenant.name if tenant else "inquilino(a)"
    days_late = (date.today() - charge.due_date).days

    owner = system.owner_name or "A administração"
    subject = (
        f"Cobrança de aluguel - {prop.description if prop else 'imóvel'} - "
        f"{charge.due_date.strftime('%m/%Y')}"
    )

    body_lines = [
        f"Olá, {tenant_name}!",
        "",
        f"Consta em nosso controle um aluguel de {_brl(charge.amount)} referente a "
        f"{charge.competence_date.strftime('%m/%Y')} do imóvel "
        f"{prop.description if prop else ''}, com vencimento em "
        f"{_brdate(charge.due_date)}, que se encontra {days_late} dia(s) em atraso.",
        "",
    ]

    if system.default_late_fee or system.default_interest_rate:
        body_lines.append(
            "Conforme o contrato de locação, incidem sobre o valor "
            f"multa de {system.default_late_fee or 0}% e juros de mora de "
            f"{system.default_interest_rate or 0}% ao mês, proporcionalmente aos "
            "dias de atraso."
        )
        body_lines.append("")

    body_lines.extend(
        [
            "Pedimos a gentileza de efetuar o pagamento o mais breve possível e, "
            "se já tiver sido realizado, desconsiderar esta mensagem.",
            "",
            "Qualquer dúvida ou dificuldade, estamos à disposição.",
            "",
            "Atenciosamente,",
            owner,
        ]
    )

    if system.owner_phone:
        body_lines.append(f"Telefone: {system.owner_phone}")
    if system.owner_email:
        body_lines.append(f"E-mail: {system.owner_email}")

    return {
        "to": tenant.email if tenant and tenant.email else None,
        "subject": subject,
        "body": "\n".join(body_lines),
    }


def send_collection_email(charge):
    """Envia o e-mail de cobrança. Retorna dict com status da operação."""
    tenant = charge.contract.tenant if charge.contract else None
    if not tenant or not tenant.email:
        raise ValueError(
            "O inquilino desta cobrança não possui e-mail cadastrado."
        )

    email_data = build_collection_email(charge)

    message = EmailMultiAlternatives(
        subject=email_data["subject"],
        body=email_data["body"],
        from_email=django_settings.DEFAULT_FROM_EMAIL,
        to=[tenant.email],
    )
    message.send(fail_silently=False)

    return {
        "sent": True,
        "to": tenant.email,
        "subject": email_data["subject"],
        "backend": django_settings.EMAIL_BACKEND.split(".")[-2],
    }
