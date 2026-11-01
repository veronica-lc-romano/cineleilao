import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.views.decorators.http import require_GET, require_POST
from django.conf import settings

from .models import Carteira, Usuario
from .services import adicionar_saldo_teste


def ler_json(request):
    try:
        dados = json.loads(request.body or "{}")
        return dados if isinstance(dados, dict) else None
    except (json.JSONDecodeError, ValueError):
        return None


def dados_usuario(usuario):
    return {
        "id": usuario.id,
        "username": usuario.username,
        "email": usuario.email,
        "papel": usuario.papel,
    }


@require_GET
@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})


@require_POST
@csrf_protect
def cadastro(request):
    dados = ler_json(request)
    if dados is None:
        return JsonResponse({"erro": "JSON inválido."}, status=400)

    username = str(dados.get("username", "")).strip()
    email = str(dados.get("email", "")).strip()
    senha = dados.get("password")
    confirmacao = dados.get("password_confirm")
    papel = str(dados.get("papel", "participante")).strip().lower()

    if not username or not email or not isinstance(senha, str):
        return JsonResponse(
            {"erro": "Informe usuário, e-mail e senha."},
            status=400,
        )

    if senha != confirmacao:
        return JsonResponse({"erro": "As senhas não coincidem."}, status=400)

    if Usuario.objects.filter(username__iexact=username).exists():
        return JsonResponse(
            {"erro": "Este nome de usuário já está em uso."},
            status=400,
        )

    if Usuario.objects.filter(email__iexact=email).exists():
        return JsonResponse({"erro": "Este e-mail já está cadastrado."}, status=400)

    usuario = Usuario(
    username=username,
    email=email,
    papel=papel,
    )

    try:
        validate_password(senha, user=usuario)
    except ValidationError as erro:
        return JsonResponse({"erros": erro.messages}, status=400)

    if papel not in [
    Usuario.Papel.PARTICIPANTE,
    Usuario.Papel.LEILOEIRO,
    ]:
        return JsonResponse(
            {"erro": "Perfil inválido. Escolha participante ou leiloeiro."},
            status=400,
        )

    usuario.set_password(senha)
    usuario.save()
    Carteira.objects.get_or_create(usuario=usuario)
    login(request, usuario)

    return JsonResponse(
        {
            "mensagem": "Cadastro realizado com sucesso.",
            "usuario": dados_usuario(usuario),
        },
        status=201,
    )


@require_POST
@csrf_protect
def entrar(request):
    dados = ler_json(request)
    if dados is None:
        return JsonResponse({"erro": "JSON inválido."}, status=400)

    username = str(dados.get("username", "")).strip()
    senha = dados.get("password")

    if not username or not isinstance(senha, str) or not senha:
        return JsonResponse(
            {"erro": "Informe usuário e senha."},
            status=400,
        )

    usuario = authenticate(request, username=username, password=senha)

    if usuario is None:
        return JsonResponse(
            {"erro": "Usuário ou senha inválidos."},
            status=401,
        )

    login(request, usuario)

    return JsonResponse({
        "mensagem": "Login realizado com sucesso.",
        "usuario": dados_usuario(usuario),
    })


@require_POST
@csrf_protect
def sair(request):
    logout(request)
    return JsonResponse({"mensagem": "Logout realizado com sucesso."})


@require_GET
def perfil(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"erro": "Autenticação necessária."},
            status=401,
        )

    return JsonResponse({"usuario": dados_usuario(request.user)})


@require_GET
def consultar_carteira(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"erro": "Autenticação necessária."},
            status=401,
        )

    carteira = Carteira.objects.get_or_create(usuario=request.user)[0]

    return JsonResponse({
        "saldo_disponivel": str(carteira.saldo_disponivel),
        "saldo_reservado": str(carteira.saldo_reservado),
        "atualizada_em": carteira.atualizada_em.isoformat(),
    })


@require_GET
def consultar_movimentacoes(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"erro": "Autenticação necessária."},
            status=401,
        )

    carteira = Carteira.objects.get_or_create(usuario=request.user)[0]

    movimentacoes = carteira.movimentacoes.all()

    return JsonResponse({
        "movimentacoes": [
            {
                "id": movimentacao.id,
                "tipo": movimentacao.tipo,
                "tipo_display": movimentacao.get_tipo_display(),
                "valor": str(movimentacao.valor),
                "descricao": movimentacao.descricao,
                "criada_em": movimentacao.criada_em.isoformat(),
            }
            for movimentacao in movimentacoes
        ]
    })

@require_POST
@csrf_protect
def adicionar_credito_teste(request):
    if not settings.DEBUG:
        return JsonResponse(
            {"erro": "Adição de créditos de teste não está disponível."},
            status=403,
        )

    if not request.user.is_authenticated:
        return JsonResponse(
            {"erro": "Autenticação necessária."},
            status=401,
        )

    dados = ler_json(request)

    if dados is None:
        return JsonResponse({"erro": "JSON inválido."}, status=400)

    try:
        carteira = adicionar_saldo_teste(
            request.user,
            dados.get("valor"),
        )
    except ValidationError as erro:
        return JsonResponse(
            {"erro": erro.messages[0] if erro.messages else str(erro)},
            status=400,
        )

    return JsonResponse({
        "mensagem": "Crédito adicionado com sucesso.",
        "saldo_disponivel": str(carteira.saldo_disponivel),
        "saldo_reservado": str(carteira.saldo_reservado),
    })