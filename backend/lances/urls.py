
from django.urls import path

from .views import LancesLeilaoView

urlpatterns = [
    path(
        "<int:leilao_id>/lances/",
        LancesLeilaoView.as_view(),
        name="lances-leilao",
    ),
]
