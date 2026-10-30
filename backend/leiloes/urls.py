
from django.urls import path

from .views import ListaCriaLeiloesView, DetalheLeilaoView

from .views import EncerrarLeilaoView

urlpatterns = [
    path("", ListaCriaLeiloesView.as_view(), name="lista-cria-leiloes"),
    path("<int:pk>/", DetalheLeilaoView.as_view(), name="detalhe-leilao"),
    path(
        "<int:pk>/encerrar/",
        EncerrarLeilaoView.as_view(),
        name="encerrar-leilao",
    ),
]
