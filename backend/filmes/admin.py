from django.contrib import admin
from .models import Filme


@admin.register(Filme)
class FilmeAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tmdb_id", "data_lancamento")
    search_fields = ("titulo", "titulo_original")
    ordering = ("titulo",)


