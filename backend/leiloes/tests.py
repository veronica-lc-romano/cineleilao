
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from usuarios.models import Usuario, Carteira, Movimentacao
from leiloes.models import Leilao
from leiloes.services import encerrar_leilao
from lances.models import Lance
from rest_framework.test import APIClient
from django.urls import reverse
from unittest.mock import patch


class EncerrarLeilaoTests(TestCase):
    def setUp(self):
        self.leiloeiro = Usuario.objects.create_user(
            username="leiloeiro_teste",
            password="senha-teste-123",
            papel="leiloeiro",
        )

        self.participante = Usuario.objects.create_user(
            username="participante_teste",
            password="senha-teste-123",
            papel="participante",
        )

        self.outro_usuario = Usuario.objects.create_user(
            username="outro_usuario",
            password="senha-teste-123",
            papel="participante",
        )

        self.carteira_participante = Carteira.objects.create(
            usuario=self.participante,
            saldo_disponivel=Decimal("930.00"),
            saldo_reservado=Decimal("70.00"),
        )

        self.carteira_leiloeiro = Carteira.objects.create(
            usuario=self.leiloeiro,
            saldo_disponivel=Decimal("100.00"),
            saldo_reservado=Decimal("0.00"),
        )

        agora = timezone.now()

        self.leilao = Leilao.objects.create(
            filme_tmdb_id=603,
            titulo="Leilão de teste",
            descricao="Leilão criado por teste automatizado",
            lance_inicial=Decimal("50.00"),
            inicio_em=agora - timedelta(hours=2),
            encerra_em=agora - timedelta(minutes=1),
            criado_por=self.leiloeiro,
            status="aberto",
        )

        self.lance = Lance.objects.create(
            leilao=self.leilao,
            participante=self.participante,
            valor=Decimal("70.00"),
        )

    def test_encerrar_leilao_com_vencedor_transfere_saldo(self):
        resultado = encerrar_leilao(
            leilao_id=self.leilao.id,
            usuario=self.leiloeiro,
        )

        self.carteira_participante.refresh_from_db()
        self.carteira_leiloeiro.refresh_from_db()
        self.leilao.refresh_from_db()

        self.assertEqual(
            self.carteira_participante.saldo_reservado,
            Decimal("0.00"),
        )
        self.assertEqual(
            self.carteira_participante.saldo_disponivel,
            Decimal("930.00"),
        )
        self.assertEqual(
            self.carteira_leiloeiro.saldo_disponivel,
            Decimal("170.00"),
        )
        self.assertEqual(self.leilao.status, "encerrado")
        self.assertIsNotNone(self.leilao.liquidado_em)
        self.assertEqual(resultado["valor_pago"], "70.00")

        
        # Verifica as movimentações financeiras.
        movimentacoes_vencedor = Movimentacao.objects.filter(
            carteira=self.carteira_participante
        )

        movimentacoes_leiloeiro = Movimentacao.objects.filter(
            carteira=self.carteira_leiloeiro
        )

        self.assertEqual(movimentacoes_vencedor.count(), 1)
        self.assertEqual(movimentacoes_leiloeiro.count(), 1)

        pagamento = movimentacoes_vencedor.get()

        self.assertEqual(
            pagamento.tipo,
            Movimentacao.Tipo.PAGAMENTO,
        )
        self.assertEqual(pagamento.valor, Decimal("70.00"))

        recebimento = movimentacoes_leiloeiro.get()

        self.assertEqual(
            recebimento.tipo,
            Movimentacao.Tipo.RECEBIMENTO
        )
        self.assertEqual(recebimento.valor, Decimal("70.00"))


    def test_encerrar_duas_vezes_nao_duplica_pagamento(self):
        encerrar_leilao(
            leilao_id=self.leilao.id,
            usuario=self.leiloeiro,
        )

        resultado_segunda_tentativa = encerrar_leilao(
            leilao_id=self.leilao.id,
            usuario=self.leiloeiro,
        )

        self.carteira_leiloeiro.refresh_from_db()

        self.assertEqual(
            self.carteira_leiloeiro.saldo_disponivel,
            Decimal("170.00"),
        )
        self.assertTrue(resultado_segunda_tentativa["ja_liquidado"])
        
        self.assertEqual(
            Movimentacao.objects.filter(
                carteira=self.carteira_participante
            ).count(),
            1,
        )

        self.assertEqual(
            Movimentacao.objects.filter(
                carteira=self.carteira_leiloeiro
            ).count(),
            1,
        )


    def test_nao_permite_encerrar_antes_do_prazo(self):
        self.leilao.encerra_em = timezone.now() + timedelta(hours=1)
        self.leilao.save(update_fields=["encerra_em"])

        with self.assertRaises(Exception):
            encerrar_leilao(
                leilao_id=self.leilao.id,
                usuario=self.leiloeiro,
            )

    def test_outro_usuario_nao_pode_encerrar(self):
        with self.assertRaises(Exception):
            encerrar_leilao(
                leilao_id=self.leilao.id,
                usuario=self.outro_usuario,
            )

    def test_encerrar_sem_lances_nao_transfere_dinheiro(self):

        self.lance.delete()

        resultado = encerrar_leilao(
            leilao_id=self.leilao.id,
            usuario=self.leiloeiro,
        )

        self.carteira_leiloeiro.refresh_from_db()
        self.leilao.refresh_from_db()

        self.assertEqual(
            self.carteira_leiloeiro.saldo_disponivel,
            Decimal("100.00"),
        )
        self.assertEqual(self.leilao.status, "encerrado")
        self.assertIsNotNone(self.leilao.liquidado_em)
        self.assertEqual(resultado["valor_pago"], "0.00")
        
        self.assertEqual(
            Movimentacao.objects.filter(
                carteira=self.carteira_participante
            ).count(),
            0,
        )

        self.assertEqual(
            Movimentacao.objects.filter(
                carteira=self.carteira_leiloeiro
            ).count(),
            0,
        )

    def test_falha_na_movimentacao_reverte_toda_a_liquidacao(self):
        with patch(
            "leiloes.services.Movimentacao.objects.create",
            side_effect=RuntimeError("Falha simulada"),
        ):
            with self.assertRaises(RuntimeError):
                encerrar_leilao(
                    leilao_id=self.leilao.id,
                    usuario=self.leiloeiro,
                )

        self.carteira_participante.refresh_from_db()
        self.carteira_leiloeiro.refresh_from_db()
        self.leilao.refresh_from_db()

        self.assertEqual(
            self.carteira_participante.saldo_reservado,
            Decimal("70.00"),
        )
        self.assertEqual(
            self.carteira_leiloeiro.saldo_disponivel,
            Decimal("100.00"),
        )
        self.assertIsNone(self.leilao.liquidado_em)
        self.assertEqual(self.leilao.status, "aberto")

        self.assertEqual(
            Movimentacao.objects.filter(
                carteira=self.carteira_participante
            ).count(),
            0,
        )
        self.assertEqual(
            Movimentacao.objects.filter(
                carteira=self.carteira_leiloeiro
            ).count(),
            0,
        )


class EncerrarLeilaoAPITests(EncerrarLeilaoTests):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.url = reverse(
            "encerrar-leilao",
            kwargs={"pk": self.leilao.pk},
        )

    def test_leiloeiro_responsavel_pode_encerrar_pela_api(self):
        self.client.force_authenticate(user=self.leiloeiro)

        resposta = self.client.post(self.url)

        self.assertEqual(resposta.status_code, 200)

        self.carteira_participante.refresh_from_db()
        self.carteira_leiloeiro.refresh_from_db()

        self.assertEqual(
            self.carteira_participante.saldo_reservado,
            Decimal("0.00"),
        )
        self.assertEqual(
            self.carteira_leiloeiro.saldo_disponivel,
            Decimal("170.00"),
        )

    def test_usuario_nao_autenticado_nao_pode_encerrar(self):
        resposta = self.client.post(self.url)

        self.assertIn(resposta.status_code, [401, 403])

    def test_outro_usuario_nao_pode_encerrar_pela_api(self):
        self.client.force_authenticate(user=self.outro_usuario)

        resposta = self.client.post(self.url)

        self.assertEqual(resposta.status_code, 403)

    def test_leilao_inexistente_retorna_404(self):
        self.client.force_authenticate(user=self.leiloeiro)

        resposta = self.client.post(
            reverse("encerrar-leilao", kwargs={"pk": 999999})
        )

        self.assertEqual(resposta.status_code, 404)

    def test_repetir_encerramento_nao_duplica_pagamento(self):
        self.client.force_authenticate(user=self.leiloeiro)

        primeira_resposta = self.client.post(self.url)
        segunda_resposta = self.client.post(self.url)

        self.assertEqual(primeira_resposta.status_code, 200)
        self.assertEqual(segunda_resposta.status_code, 200)

        self.carteira_leiloeiro.refresh_from_db()

        self.assertEqual(
            self.carteira_leiloeiro.saldo_disponivel,
            Decimal("170.00"),
        )

