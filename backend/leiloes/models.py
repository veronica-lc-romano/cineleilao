
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from decimal import Decimal



class Leilao(models.Model):
    class Status(models.TextChoices):
        AGENDADO = "agendado", "Agendado"
        ABERTO = "aberto", "Aberto"
        ENCERRADO = "encerrado", "Encerrado"
        CANCELADO = "cancelado", "Cancelado"

    filme_tmdb_id = models.PositiveIntegerField()
    poster_path = models.CharField(max_length=255, blank=True)
    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)

    lance_inicial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )

    inicio_em = models.DateTimeField()
    encerra_em = models.DateTimeField()

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="leiloes_criados",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AGENDADO,
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    liquidado_em = models.DateTimeField(
    null=True,
    blank=True,
    editable=False,
    )

    class Meta:
        ordering = ["inicio_em"]



    @property
    def status_atual(self):
        agora = timezone.now()

        if self.status == self.Status.CANCELADO:
            return self.Status.CANCELADO

        if agora < self.inicio_em:
            return self.Status.AGENDADO

        if agora >= self.encerra_em:
            return self.Status.ENCERRADO

        return self.Status.ABERTO

    @property
    def esta_aberto(self):
        return self.status_atual == self.Status.ABERTO

    
    def __str__(self):
        return f"{self.titulo} (#{self.pk})"

