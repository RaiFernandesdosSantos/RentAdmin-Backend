from django.core.exceptions import ValidationError


def validate_not_blank(value):
    if isinstance(value, str) and not value.strip():
        raise ValidationError("O valor não pode ser apenas espaços em branco.")
