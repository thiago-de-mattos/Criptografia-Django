"""
Helpers de mascaramento de dados sensiveis.

Diferente da criptografia (fields.py), isso NAO protege o dado em
repouso -- o dado real continua guardado (criptografado) no banco.
Mascaramento e so pra CONTROLE DE EXIBICAO: decide quanto do valor
real mostrar pra quem esta vendo a tela/relatorio.

Fluxo tipico:
    valor_real = prontuario.cpf          # Django descriptografa
    valor_exibido = mask_cpf(valor_real) # so entao mascara pra tela
"""

import re


def mask_cpf(cpf: str) -> str:
    """
    '123.456.789-00' ou '12345678900' -> '***.***.789-00'
    Mostra so os ultimos 4 digitos (bloco antes do traço + digitos verificadores).
    """
    digits = re.sub(r"\D", "", cpf or "")
    if len(digits) != 11:
        return "***.***.***-**"
    return f"***.***.{digits[6:9]}-{digits[9:]}"


def mask_nome(nome: str) -> str:
    """
    'Maria da Silva' -> 'Maria d* S*****'
    Mantem a primeira palavra inteira (costuma ser o nome de tratamento)
    e reduz as demais a inicial + asteriscos.
    """
    if not nome:
        return ""
    partes = nome.strip().split()
    if len(partes) <= 1:
        return partes[0] if partes else ""
    primeira, *resto = partes
    resto_mascarado = [
        p[0] + "*" * (len(p) - 1) if len(p) > 1 else p
        for p in resto
    ]
    return " ".join([primeira, *resto_mascarado])


def mask_telefone(telefone: str) -> str:
    """
    '(21) 98765-4321' -> '(21) *****-4321'
    """
    digits = re.sub(r"\D", "", telefone or "")
    if len(digits) < 4:
        return "*" * len(digits)
    return f"{'*' * (len(digits) - 4)}{digits[-4:]}"


def mask_email(email: str) -> str:
    """
    'maria.silva@exemplo.com' -> 'ma***@exemplo.com'
    """
    if not email or "@" not in email:
        return "***"
    usuario, dominio = email.split("@", 1)
    if len(usuario) <= 2:
        usuario_mascarado = usuario[0] + "*"
    else:
        usuario_mascarado = usuario[:2] + "*" * (len(usuario) - 2)
    return f"{usuario_mascarado}@{dominio}"