from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Carteira, Movimentacao, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Dados do leilão", {"fields": ("papel",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Dados do leilão", {"fields": ("papel",)}),
    )


@admin.register(Carteira)
class CarteiraAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "saldo_disponivel",
        "saldo_reservado",
        "atualizada_em",
    )
    search_fields = ("usuario__username",)


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = (
        "carteira",
        "tipo",
        "valor",
        "descricao",
        "criada_em",
    )
    list_filter = ("tipo",)
    search_fields = ("carteira__usuario__username", "descricao")
    readonly_fields = ("carteira", "tipo", "valor", "descricao", "criada_em")


# Register your models here.
