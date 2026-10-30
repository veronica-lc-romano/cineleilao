
from django.urls import path

from . import views

urlpatterns = [
    path("csrf/", views.csrf_token, name="csrf-token"),
    path("cadastro/", views.cadastro, name="cadastro"),
    path("login/", views.entrar, name="login"),
    path("logout/", views.sair, name="logout"),
    path("me/", views.perfil, name="perfil"),
]
