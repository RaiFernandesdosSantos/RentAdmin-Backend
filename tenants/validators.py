from django.core.exceptions import ValidationError
import re


def validate_cpf(value):
    cpf = re.sub(r"\D", "", value)

    if len(cpf) != 11:
        raise ValidationError("CPF deve conter 11 dígitos.")

    if cpf in (c * 11 for c in "0123456789"):
        raise ValidationError("CPF inválido: todos os dígitos são iguais.")

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11

    soma2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto2 = (soma2 * 10) % 11

    if resto != int(cpf[9]) or resto2 != int(cpf[10]):
        raise ValidationError("CPF inválido: dígitos verificadores não conferem.")
