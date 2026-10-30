from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .services import buscar_filmes


@api_view(["GET"])
def pesquisar_filmes(request):
    termo = request.query_params.get("q", "").strip()

    if len(termo) < 2:
        return Response(
            {"erro": "Informe pelo menos 2 caracteres para pesquisar."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        pagina = int(request.query_params.get("pagina", "1"))
        if pagina < 1:
            raise ValueError
    except ValueError:
        return Response(
            {"erro": "O parâmetro pagina deve ser um inteiro positivo."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        resultado = buscar_filmes(termo, pagina)
    except RuntimeError as erro:
        return Response(
            {"erro": str(erro)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception:
        return Response(
            {"erro": "Não foi possível consultar o TMDB neste momento."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    filmes = [
        {
            "tmdb_id": filme["id"],
            "titulo": filme.get("title", ""),
            "titulo_original": filme.get("original_title", ""),
            "sinopse": filme.get("overview", ""),
            "data_lancamento": filme.get("release_date") or None,
            "poster_path": filme.get("poster_path") or "",
        }
        for filme in resultado.get("results", [])
    ]

    return Response({
        "pagina": resultado.get("page", pagina),
        "total_paginas": resultado.get("total_pages", 0),
        "total_resultados": resultado.get("total_results", 0),
        "resultados": filmes,
    })


# Create your views here.
