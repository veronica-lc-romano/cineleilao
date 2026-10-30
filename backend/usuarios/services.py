
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from .models import Carteira, Movimentacao


def _validar_valor(valor):
    try:
        valor = Decimal(str(valor))
    except Exception as erro:
        raise ValidationError("Informe um valor monetário válido.") from erro

    if not valor.is_finite() or valor <= Decimal("0.00"):
        raise ValidationError("O valor deve ser maior que zero.")

    if valor.as_tuple().exponent < -2:
        raise ValidationError(
            "O valor deve ter no máximo duas casas decimais."
        )

    return valor


def obter_ou_criar_carteira(usuario):
    carteira, _ = Carteira.objects.get_or_create(usuario=usuario)
    return carteira


@transaction.atomic
def adicionar_saldo_teste(usuario, valor):
    """Adiciona saldo fictício para desenvolvimento e testes."""
    valor = _validar_valor(valor)
    carteira = obter_ou_criar_carteira(usuario)

    carteira = Carteira.objects.select_for_update().get(pk=carteira.pk)

    carteira.saldo_disponivel = F("saldo_disponivel") + valor
    carteira.save(update_fields=["saldo_disponivel", "atualizada_em"])
    carteira.refresh_from_db()

    Movimentacao.objects.create(
        carteira=carteira,
        tipo=Movimentacao.Tipo.DEPOSITO,
        valor=valor,
        descricao="Crédito fictício para testes",
    )

    return carteira


@transaction.atomic
def reservar_saldo(usuario, valor, descricao="Reserva para lance"):
    valor = _validar_valor(valor)
    carteira = Carteira.objects.select_for_update().get(usuario=usuario)

    if carteira.saldo_disponivel < valor:
        raise ValidationError("Saldo disponível insuficiente.")

    carteira.saldo_disponivel -= valor
    carteira.saldo_reservado += valor
    carteira.save(
        update_fields=["saldo_disponivel", "saldo_reservado", "atualizada_em"]
    )

    Movimentacao.objects.create(
        carteira=carteira,
        tipo=Movimentacao.Tipo.RESERVA,
        valor=valor,
        descricao=descricao,
    )

    return carteira


@transaction.atomic
def liberar_reserva(usuario, valor, descricao="Liberação de reserva"):
    valor = _validar_valor(valor)
    carteira = Carteira.objects.select_for_update().get(usuario=usuario)

    if carteira.saldo_reservado < valor:
        raise ValidationError("Saldo reservado insuficiente.")

    carteira.saldo_reservado -= valor
    carteira.saldo_disponivel += valor
    carteira.save(
        update_fields=["saldo_disponivel", "saldo_reservado", "atualizada_em"]
    )

    Movimentacao.objects.create(
        carteira=carteira,
        tipo=Movimentacao.Tipo.LIBERACAO,
        valor=valor,
        descricao=descricao,
    )

    return carteira
