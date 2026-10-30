from django.db import models

class Filme(models.Model):
    tmdb_id = models.PositiveIntegerField(unique=True)
    titulo = models.CharField(max_length=255)
    titulo_original = models.CharField(max_length=255, blank=True)
    sinopse = models.TextField(blank=True)
    data_lancamento = models.DateField(null=True, blank=True)
    poster_path = models.CharField(max_length=255, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["titulo"]

    def __str__(self):
        return self.titulo


# Create your models here.
