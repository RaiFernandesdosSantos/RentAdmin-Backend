from django.core.exceptions import ValidationError
import re


def validate_zip(value):
    if not re.match(r"^\d{8}$", str(value.strip().replace("-", ""))):
        raise ValidationError("O CEP deve conter exatamente 8 dígitos numéricos.")
