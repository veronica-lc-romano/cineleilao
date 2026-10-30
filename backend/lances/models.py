
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from decimal import Decimal


class Lance(models.Model):
    leilao = models.ForeignKey(
        "leiloes.Leilao",
        on_delete=models.PROTECT,
        related_name="lances",
    )
    participante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="lances",
    )
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-valor", "criado_em"]

    def __str__(self):
        return f"Lance de R$ {self.valor} no leilão #{self.leilao_id}"
