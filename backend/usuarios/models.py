from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Carteira(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="carteira",
    )
    saldo_disponivel = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    saldo_reservado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carteira de {self.usuario.username}"



class Movimentacao(models.Model):
    class Tipo(models.TextChoices):
        DEPOSITO = "deposito", "Depósito"
        RESERVA = "reserva", "Reserva de lance"
        LIBERACAO = "liberacao", "Liberação de reserva"
        PAGAMENTO = "pagamento", "Pagamento de leilão"
        RECEBIMENTO = "recebimento", "Recebimento de leilão"
        ESTORNO = "estorno", "Estorno"

    carteira = models.ForeignKey(
        Carteira,
        on_delete=models.PROTECT,
        related_name="movimentacoes",
    )
    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
    )
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    descricao = models.CharField(max_length=255)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criada_em"]

    def __str__(self):
        return f"{self.get_tipo_display()} - R$ {self.valor}"


class Usuario(AbstractUser):
    class Papel(models.TextChoices):
        LEILOEIRO = "leiloeiro", "Leiloeiro"
        PARTICIPANTE = "participante", "Participante"

    papel = models.CharField(
        max_length=20,
        choices=Papel.choices,
        default=Papel.PARTICIPANTE,
    )

    def __str__(self):
        return f"{self.username} ({self.get_papel_display()})"
