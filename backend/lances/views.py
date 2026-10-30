from django.shortcuts import render
from django.core.exceptions import ValidationError as DjangoValidationError

from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from leiloes.models import Leilao
from usuarios.services import reservar_saldo, liberar_reserva

from .models import Lance
from .serializers import LanceSerializer


class LancesLeilaoView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, leilao_id):
        leilao = get_object_or_404(Leilao, pk=leilao_id)

        lances = (
            Lance.objects
            .filter(leilao=leilao)
            .select_related("participante")
            .order_by("-valor", "criado_em")
        )

        return Response(LanceSerializer(lances, many=True).data)


    def post(self, request, leilao_id):
        if request.user.papel != "participante":
            raise PermissionDenied(
                "Somente participantes podem dar lances."
            )

        try:
            valor = Decimal(str(request.data.get("valor", "")))
        except Exception:
            raise ValidationError({
                "valor": "Informe um valor numérico válido."
            })

        if not valor.is_finite() or valor <= 0:
            raise ValidationError({
                "valor": "O lance deve ser maior que zero."
            })

        if valor.quantize(Decimal("0.01")) != valor:
            raise ValidationError({
                "valor": "O lance deve ter no máximo duas casas decimais."
            })

        try:
            with transaction.atomic():
                try:
                    leilao = (
                        Leilao.objects
                        .select_for_update()
                        .get(pk=leilao_id)
                    )
                except Leilao.DoesNotExist:
                    raise NotFound("Leilão não encontrado.")

                if not leilao.esta_aberto:
                    raise ValidationError({
                        "leilao": "Este leilão não está aceitando lances."
                    })

                maior_lance = (
                    Lance.objects
                    .filter(leilao=leilao)
                    .select_related("participante")
                    .order_by("-valor", "criado_em")
                    .first()
                )

                minimo = (
                    maior_lance.valor
                    if maior_lance
                    else leilao.lance_inicial
                )

                if valor < minimo or (
                    maior_lance is not None and valor <= minimo
                ):
                    raise ValidationError({
                        "valor": (
                            f"O lance deve ser superior a R$ {minimo:.2f}."
                            if maior_lance
                            else f"O lance mínimo é R$ {minimo:.2f}."
                        )
                    })

                if (
                    maior_lance
                    and maior_lance.participante_id == request.user.id
                ):
                    liberar_reserva(
                        request.user,
                        maior_lance.valor,
                        descricao=(
                            f"Substituição de reserva do leilão #{leilao.id}"
                        ),
                    )

                reservar_saldo(
                    request.user,
                    valor,
                    descricao=f"Reserva para lance no leilão #{leilao.id}",
                )

                if (
                    maior_lance
                    and maior_lance.participante_id != request.user.id
                ):
                    liberar_reserva(
                        maior_lance.participante,
                        maior_lance.valor,
                        descricao=f"Lance superado no leilão #{leilao.id}",
                    )

                lance = Lance.objects.create(
                    leilao=leilao,
                    participante=request.user,
                    valor=valor,
                )

        except DjangoValidationError as erro:
            raise ValidationError({
                "detail": erro.messages
            })

        return Response(
            LanceSerializer(lance).data,
            status=status.HTTP_201_CREATED,
        )
