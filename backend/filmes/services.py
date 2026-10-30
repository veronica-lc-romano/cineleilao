
import os

import requests


TMDB_BASE_URL = "https://api.themoviedb.org/3"


def buscar_filmes(termo, pagina=1):
    api_key = os.getenv("TMDB_API_KEY")

    if not api_key:
        raise RuntimeError(
            "A variável TMDB_API_KEY não está configurada."
        )

    resposta = requests.get(
        f"{TMDB_BASE_URL}/search/movie",
        params={
            "api_key": api_key,
            "query": termo,
            "language": "pt-BR",
            "page": pagina,
            "include_adult": False,
        },
        timeout=10,
    )

    resposta.raise_for_status()
    return resposta.json()

