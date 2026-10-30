from django.urls import path
from .views import pesquisar_filmes


urlpatterns = [
    path("pesquisar/", pesquisar_filmes, name="pesquisar-filmes"),
]
