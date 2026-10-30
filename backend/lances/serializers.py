
from rest_framework import serializers

from .models import Lance


class LanceSerializer(serializers.ModelSerializer):
    participante_username = serializers.CharField(
        source="participante.username",
        read_only=True,
    )

    class Meta:
        model = Lance
        fields = [
            "id",
            "leilao",
            "participante",
            "participante_username",
            "valor",
            "criado_em",
        ]
        read_only_fields = [
            "id",
            "leilao",
            "participante",
            "participante_username",
            "criado_em",
        ]
