from django.core.exceptions import ValidationError


def validate_positive(value):
    if isinstance(value, (int, float)) and value < 0:
        raise ValidationError("O valor deve ser positivo.")


def validate_minimum(value, minimum):
    if isinstance(value, (int, float)) and value < minimum:
        raise ValidationError(f"O valor deve ser maior ou igual a {minimum}.")
