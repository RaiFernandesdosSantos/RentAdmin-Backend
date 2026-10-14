"""Emissão de arquivos — geração de documentos do sistema (PDF).

Atualmente gera o Contrato de Locação em PDF a partir dos dados do
contrato, do imóvel, do inquilino e das configurações do sistema.
"""
from fpdf import FPDF

from system.models import SystemSettings


def _brl(value):
    """Formata um valor como moeda brasileira (R$ 1.234,56)."""
    try:
        text = f"{value:,.2f}"
    except (TypeError, ValueError):
        return "—"
    return "R$ " + text.replace(",", "X").replace(".", ",").replace("X", ".")


def _brdate(value):
    if not value:
        return "—"
    return value.strftime("%d/%m/%Y")


def build_contract_pdf(contract) -> bytes:
    """Gera o PDF do contrato de locação e retorna os bytes do arquivo."""
    settings = SystemSettings.get()
    prop = contract.property
    tenant = contract.tenant
    guarantor = contract.guarantor

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    ## ------------------------------------------------------------------
    ## Título
    pdf.set_font("helvetica", "B", 15)
    pdf.cell(0, 10, "CONTRATO DE LOCAÇÃO", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(
        0,
        7,
        f"Locação {prop.get_property_type_display()}",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(3)

    def section(title):
        pdf.ln(2)
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")

    def line(label, value=""):
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(52, 5.5, label)
        pdf.set_font("helvetica", "", 9)
        pdf.multi_cell(0, 5.5, str(value), new_x="LMARGIN", new_y="NEXT")

    ## ------------------------------------------------------------------
    ## Identificação das partes
    section("IDENTIFICAÇÃO DAS PARTES")
    line("LOCADOR:", settings.owner_name or "____________________________")
    line("CPF/CNPJ:", settings.owner_cpf or "____________________________")
    if settings.owner_phone:
        line("TELEFONE:", settings.owner_phone)
    if settings.owner_email:
        line("E-MAIL:", settings.owner_email)
    pdf.ln(1)
    line("LOCATÁRIO:", tenant.name)
    line("CPF:", tenant.cpf)
    line("PROFISSÃO:", tenant.profession)
    line("RENDA MENSAL:", _brl(tenant.monthly_income))
    line("TELEFONE:", tenant.phone_number)
    if tenant.email:
        line("E-MAIL:", tenant.email)
    if guarantor:
        pdf.ln(1)
        line("FIADOR:", guarantor.name)
        line("CPF:", guarantor.cpf)
        line("PROFISSÃO:", guarantor.profession)
        line("RENDA MENSAL:", _brl(guarantor.monthly_income))

    ## ------------------------------------------------------------------
    ## Objeto
    section("OBJETO DA LOCAÇÃO")
    line("IMÓVEL:", prop.description)
    line(
        "ENDEREÇO:",
        f"{prop.street}, nº {prop.number} - {prop.neighborhood}, "
        f"CEP {prop.zip_code}",
    )
    line("MATRÍCULA:", prop.registration)
    if prop.square_meters:
        line("ÁREA:", f"{prop.square_meters} m²")

    ## ------------------------------------------------------------------
    ## Valores e condições
    section("VALORES E CONDIÇÕES")
    line("ALUGUEL MENSAL:", _brl(contract.monthly_rent))
    line("DIA DE VENCIMENTO:", f"dia {contract.due_day} de cada mês")
    line(
        "CAUÇÃO:",
        _brl(contract.security_deposit) if contract.security_deposit else "Não há",
    )
    line("INÍCIO DA VIGÊNCIA:", _brdate(contract.start_date))
    line("FIM DA VIGÊNCIA:", _brdate(contract.end_date))
    line("ÍNDICE DE REAJUSTE:", settings.default_adjustment_index or "—")
    if settings.default_late_fee:
        line("MULTA POR ATRASO:", f"{settings.default_late_fee}%")
    if settings.default_interest_rate:
        line("JUROS DE MORA:", f"{settings.default_interest_rate}% ao mês")

    ## ------------------------------------------------------------------
    ## Cláusulas
    section("CLÁUSULAS E CONDIÇÕES")
    clauses = [
        "Cláusula 1ª - DO OBJETO. O LOCADOR declara ser legítimo possuidor do imóvel "
        "acima descrito e o loca ao LOCATÁRIO por livre e espontânea vontade, que o "
        "recebe para o fim declarado, comprometendo-se a devolvê-lo no estado em que "
        "o recebe, salvo as deteriorias naturais ao uso regular.",
        "Cláusula 2ª - DO ALUGUEL. O LOCATÁRIO pagará ao LOCADOR, mensalmente, o "
        f"aluguel de {_brl(contract.monthly_rent)}, com vencimento no dia "
        f"{contract.due_day} de cada mês, mediante depósito/transferência na conta "
        "bancária indicada pelo LOCADOR, independentemente de notificação ou cobrança.",
        "Cláusula 3ª - DO REAJUSTE. O valor do aluguel será reajustado anualmente, na "
        f"data-base do contrato, pelo índice {settings.default_adjustment_index or 'acordado entre as partes'}.",
        "Cláusula 4ª - DA CONSERVAÇÃO. Correrão por conta do LOCATÁRIO as despesas "
        "ordinárias de conservação e manutenção do imóvel decorrentes de sua ocupação, "
        "tais como água, energia, limpeza e pequenos reparos, cabendo ao LOCADOR as "
        "despesas extraordinárias e estruturais.",
        "Cláusula 5ª - DA VIGÊNCIA. O presente contrato tem vigência de "
        f"{_brdate(contract.start_date)} a {_brdate(contract.end_date)}. Findo o "
        "prazo, o contrato poderá ser renovado por acordo entre as partes, e o LOCATÁRIO "
        "ficará obrigado a restituir o imóvel caso não haja renovação.",
        "Cláusula 6ª - DA MULTA E DOS JUROS. O atraso no pagamento do aluguel "
        f"sujeitará o LOCATÁRIO à multa de {settings.default_late_fee or 0}% sobre o "
        f"valor devido, além de juros de mora de {settings.default_interest_rate or 0}% "
        "ao mês, proporcionalmente aos dias de atraso.",
        "Cláusula 7ª - DO FORO. Fica eleito o foro da comarca da situação do imóvel "
        "para dirimir quaisquer dúvidas oriundas do presente contrato, com renúncia "
        "expressa a qualquer outro, por mais privilegiado que seja.",
    ]
    pdf.set_font("helvetica", "", 9)
    for clause in clauses:
        pdf.multi_cell(0, 5, clause, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1.5)

    ## ------------------------------------------------------------------
    ## Assinaturas
    pdf.ln(10)
    pdf.set_font("helvetica", "I", 9)
    pdf.cell(
        0,
        5,
        f"Local e data: ____________________, ____ de ______________ de ______",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(14)

    col_w = pdf.epw / 2
    y = pdf.get_y()

    def signature(x, label):
        pdf.set_draw_color(120, 120, 120)
        pdf.line(x + 4, y, x + col_w - 8, y)
        pdf.set_xy(x, y + 2)
        pdf.set_font("helvetica", "", 9)
        pdf.cell(col_w - 8, 5, label, align="C")

    signature(pdf.l_margin, "LOCADOR")
    signature(pdf.l_margin + col_w, "LOCATÁRIO")

    if guarantor:
        pdf.ln(14)
        y = pdf.get_y()
        signature(pdf.l_margin + col_w / 2, "FIADOR")

    return bytes(pdf.output())
