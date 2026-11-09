import re


def normalizar_periodo(valor):
    """Devuelve los periodos académicos con el formato AAAA-S."""
    if valor is None:
        return None

    texto = str(valor).strip()
    if re.fullmatch(r"\d{4}[12]", texto):
        return f"{texto[:4]}-{texto[4:]}"
    if re.fullmatch(r"\d{4}-[12]", texto):
        return texto
    return texto
