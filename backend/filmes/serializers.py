from rest_framework import serializers

from .models import Filme


class FilmeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filme
        fields = [
            "id",
            "tmdb_id",
            "titulo",
            "titulo_original",
            "sinopse",
            "data_lancamento",
            "poster_path",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = fields
