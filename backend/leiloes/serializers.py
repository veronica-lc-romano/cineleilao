
from rest_framework import serializers
from django.utils import timezone

from .models import Leilao


class LeilaoSerializer(serializers.ModelSerializer):
    criado_por_username = serializers.CharField(
        source="criado_por.username",
        read_only=True,
    )
    status = serializers.SerializerMethodField()

    class Meta:
        model = Leilao
        fields = [
            "id",
            "filme_tmdb_id",
            "titulo",
            "descricao",
            "lance_inicial",
            "inicio_em",
            "encerra_em",
            "criado_por",
            "criado_por_username",
            "status",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "id",
            "criado_por",
            "status",
            "criado_em",
            "atualizado_em",
        ]

    def get_status(self, obj):
        return obj.status_atual

    def validate(self, attrs):
        inicio = attrs.get("inicio_em")
        encerramento = attrs.get("encerra_em")

        if inicio and encerramento and encerramento <= inicio:
            raise serializers.ValidationError({
                "encerra_em": "O encerramento deve ser posterior ao início."
            })

        if inicio and inicio < timezone.now():
            raise serializers.ValidationError({
                "inicio_em": "O início não pode estar no passado."
            })

        return attrs

