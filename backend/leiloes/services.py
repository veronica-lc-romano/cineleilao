
from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)

from leiloes.models import Leilao
from lances.models import Lance
from usuarios.models import Carteira, Movimentacao


@transaction.atomic
def encerrar_leilao(leilao_id, usuario):
    # Impede duas liquidações simultâneas do mesmo leilão.
    try:
        leilao = (
            Leilao.objects
            .select_for_update()
            .get(pk=leilao_id)
        )
    except Leilao.DoesNotExist:
        raise NotFound("Leilão não encontrado.")

    # Apenas o responsável pelo leilão pode encerrá-lo.
    if leilao.criado_por_id != usuario.pk:
        raise PermissionDenied(
            "Somente o leiloeiro responsável pode encerrar este leilão."
        )

    # Idempotência: não repetir uma liquidação concluída.
    if leilao.liquidado_em is not None:
        return {
            "leilao_id": leilao.pk,
            "status": "encerrado",
            "liquidado": True,
            "ja_liquidado": True,
            "valor_pago": "0.00",
            "mensagem": "Este leilão já foi liquidado anteriormente.",
        }

    if leilao.status == "cancelado":
        raise ValidationError("Um leilão cancelado não pode ser liquidado.")

    agora = timezone.now()

    if agora < leilao.encerra_em:
        raise ValidationError(
            "O leilão ainda não atingiu o horário previsto de encerramento."
        )

    # O primeiro lance é o maior, conforme a ordenação do modelo.
    lance_vencedor = (
        Lance.objects
        .filter(leilao=leilao)
        .select_related("participante")
        .order_by("-valor", "criado_em", "pk")
        .first()
    )

    # Sem lances: encerrar sem movimentar dinheiro.
    if lance_vencedor is None:
        leilao.status = "encerrado"
        leilao.liquidado_em = agora
        leilao.save(update_fields=["status", "liquidado_em"])

        return {
            "leilao_id": leilao.pk,
            "status": "encerrado",
            "liquidado": True,
            "ja_liquidado": False,
            "valor_pago": "0.00",
            "mensagem": "Leilão encerrado sem lances e sem pagamento.",
        }

    valor = lance_vencedor.valor

    # Garantir que existam carteiras para os dois usuários.
    carteira_vencedor, _ = Carteira.objects.get_or_create(
        usuario=lance_vencedor.participante
    )
    carteira_leiloeiro, _ = Carteira.objects.get_or_create(
        usuario=leilao.criado_por
    )

    # Bloquear as carteiras em ordem fixa para reduzir risco de deadlock.
    ids_carteiras = sorted([
        carteira_vencedor.pk,
        carteira_leiloeiro.pk,
    ])

    carteiras = {
        carteira.pk: carteira
        for carteira in (
            Carteira.objects
            .select_for_update()
            .filter(pk__in=ids_carteiras)
            .order_by("pk")
        )
    }

    carteira_vencedor = carteiras[carteira_vencedor.pk]
    carteira_leiloeiro = carteiras[carteira_leiloeiro.pk]

    if carteira_vencedor.saldo_reservado < valor:
        raise ValidationError(
            "O saldo reservado do vencedor é insuficiente para liquidar o lance."
        )

    # Transferência integral, sem comissão da plataforma.
    carteira_vencedor.saldo_reservado -= valor
    carteira_leiloeiro.saldo_disponivel += valor

    carteira_vencedor.save(
        update_fields=["saldo_reservado", "atualizada_em"]
    )
    carteira_leiloeiro.save(
        update_fields=["saldo_disponivel", "atualizada_em"]
    )

    # Registra o débito na carteira do vencedor.
    Movimentacao.objects.create(
        carteira=carteira_vencedor,
        tipo=Movimentacao.Tipo.PAGAMENTO,
        valor=valor,
        descricao=f"Pagamento do leilão #{leilao.pk} — lance vencedor",
    )

    Movimentacao.objects.create(
        carteira=carteira_leiloeiro,
        tipo=Movimentacao.Tipo.RECEBIMENTO,
        valor=valor,
        descricao=f"Recebimento do leilão #{leilao.pk}",
    )

    # Marcar como liquidado na mesma transação da transferência.
    leilao.status = "encerrado"
    leilao.liquidado_em = agora
    leilao.save(update_fields=["status", "liquidado_em"])

    return {
        "leilao_id": leilao.pk,
        "status": "encerrado",
        "liquidado": True,
        "ja_liquidado": False,
        "vencedor": lance_vencedor.participante.username,
        "valor_pago": str(valor),
        "mensagem": "Leilão encerrado e pagamento integral efetuado.",
    }
