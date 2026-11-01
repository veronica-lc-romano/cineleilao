from django.urls import path

from . import views

urlpatterns = [
    path("csrf/", views.csrf_token, name="csrf-token"),
    path("cadastro/", views.cadastro, name="cadastro"),
    path("login/", views.entrar, name="login"),
    path("logout/", views.sair, name="logout"),
    path("me/", views.perfil, name="perfil"),
    path("carteira/", views.consultar_carteira, name="consultar-carteira"),
    path(
        "movimentacoes/",
        views.consultar_movimentacoes,
        name="consultar-movimentacoes",
    ),
    path(
    "carteira/adicionar-credito/",
    views.adicionar_credito_teste,
    name="adicionar-credito-teste",
    ),
]
