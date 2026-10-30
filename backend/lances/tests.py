
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse

from usuarios.models import Usuario, Carteira, Movimentacao
from leiloes.models import Leilao
from lances.models import Lance


class LancesLeilaoAPITests(APITestCase):
    def setUp(self):
        agora = timezone.now()

        self.leiloeiro = Usuario.objects.create_user(
            username="leiloeiro_teste",
            password="SenhaTeste123!",
            papel="leiloeiro",
        )

        self.participante1 = Usuario.objects.create_user(
            username="participante1",
            password="SenhaTeste123!",
            papel="participante",
        )

        self.participante2 = Usuario.objects.create_user(
            username="participante2",
            password="SenhaTeste123!",
            papel="participante",
        )

        self.carteira1 = Carteira.objects.create(
            usuario=self.participante1,
            saldo_disponivel=Decimal("1000.00"),
            saldo_reservado=Decimal("0.00"),
        )

        self.carteira2 = Carteira.objects.create(
            usuario=self.participante2,
            saldo_disponivel=Decimal("1000.00"),
            saldo_reservado=Decimal("0.00"),
        )

        self.leilao = Leilao.objects.create(
            filme_tmdb_id=550,
            titulo="Filme de teste",
            descricao="LeilÃ£o criado para testes automatizados",
            lance_inicial=Decimal("50.00"),
            inicio_em=agora - timedelta(minutes=5),
            encerra_em=agora + timedelta(hours=1),
            criado_por=self.leiloeiro,
            status="aberto",
        )

        self.url = reverse(
            "lances-leilao",
            kwargs={"leilao_id": self.leilao.id},
        )

    def dar_lance(self, usuario, valor):
        self.client.force_authenticate(user=usuario)
        return self.client.post(
            self.url,
            {"valor": str(valor)},
            format="json",
        )

    def test_participante_pode_dar_primeiro_lance(self):
        resposta = self.dar_lance(self.participante1, "50.00")

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(Lance.objects.filter(leilao=self.leilao).count(), 1)

        self.carteira1.refresh_from_db()

        self.assertEqual(
            self.carteira1.saldo_disponivel,
            Decimal("950.00"),
        )
        self.assertEqual(
            self.carteira1.saldo_reservado,
            Decimal("50.00"),
        )

        self.assertTrue(
            Movimentacao.objects.filter(
                carteira=self.carteira1,
                tipo=Movimentacao.Tipo.RESERVA,
                valor=Decimal("50.00"),
            ).exists()
        )

    def test_lance_superior_libera_reserva_do_lance_anterior(self):
        primeira_resposta = self.dar_lance(
            self.participante1,
            "50.00",
        )
        self.assertEqual(primeira_resposta.status_code, 201)

        segunda_resposta = self.dar_lance(
            self.participante2,
            "70.00",
        )
        self.assertEqual(segunda_resposta.status_code, 201)

        self.carteira1.refresh_from_db()
        self.carteira2.refresh_from_db()

        self.assertEqual(
            self.carteira1.saldo_disponivel,
            Decimal("1000.00"),
        )
        self.assertEqual(
            self.carteira1.saldo_reservado,
            Decimal("0.00"),
        )

        self.assertEqual(
            self.carteira2.saldo_disponivel,
            Decimal("930.00"),
        )
        self.assertEqual(
            self.carteira2.saldo_reservado,
            Decimal("70.00"),
        )

        maior_lance = Lance.objects.filter(
            leilao=self.leilao
        ).order_by("-valor", "criado_em").first()

        self.assertEqual(
            maior_lance.participante_id,
            self.participante2.id,
        )
        self.assertEqual(maior_lance.valor, Decimal("70.00"))

    def test_lance_abaixo_do_minimo_e_rejeitado(self):
        resposta = self.dar_lance(self.participante1, "49.00")

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(Lance.objects.count(), 0)

    def test_lance_igual_ao_maior_lance_e_rejeitado(self):
        primeira_resposta = self.dar_lance(
            self.participante1,
            "60.00",
        )
        self.assertEqual(primeira_resposta.status_code, 201)

        segunda_resposta = self.dar_lance(
            self.participante2,
            "60.00",
        )

        self.assertEqual(segunda_resposta.status_code, 400)
        self.assertEqual(Lance.objects.count(), 1)

    def test_valor_zero_e_rejeitado(self):
        resposta = self.dar_lance(self.participante1, "0.00")

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(Lance.objects.count(), 0)

    def test_valor_com_mais_de_duas_casas_decimais_e_rejeitado(self):
        resposta = self.dar_lance(self.participante1, "50.001")

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(Lance.objects.count(), 0)

    def test_usuario_nao_autenticado_nao_pode_dar_lance(self):
        resposta = self.client.post(
            self.url,
            {"valor": "50.00"},
            format="json",
        )

        self.assertIn(resposta.status_code, [401, 403])
        self.assertEqual(Lance.objects.count(), 0)

    def test_leiloeiro_nao_pode_dar_lance(self):
        resposta = self.dar_lance(self.leiloeiro, "50.00")

        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(Lance.objects.count(), 0)

    def test_lance_em_leilao_inexistente_retorna_404(self):
        self.client.force_authenticate(user=self.participante1)

        url_inexistente = reverse(
            "lances-leilao",
            kwargs={"leilao_id": 999999},
        )

        resposta = self.client.post(
            url_inexistente,
            {"valor": "50.00"},
            format="json",
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(Lance.objects.count(), 0)

    def test_listagem_de_lances_e_publica(self):
        Lance.objects.create(
            leilao=self.leilao,
            participante=self.participante1,
            valor=Decimal("60.00"),
        )

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.data), 1)
        self.assertEqual(resposta.data[0]["valor"], "60.00")

    def test_lance_com_saldo_insuficiente(self):
        self.carteira1.saldo_disponivel = Decimal("10.00")
        self.carteira1.save(update_fields=["saldo_disponivel"])

        self.client.force_authenticate(user=self.participante1)

        movimentacoes_antes = Movimentacao.objects.filter(
            carteira=self.carteira1
        ).count()

        resposta = self.client.post(
            self.url,
            {"valor": "100.00"},
            format="json",
        )

        self.assertEqual(resposta.status_code, 400)

        self.assertFalse(
            Lance.objects.filter(
                leilao=self.leilao,
                participante=self.participante1,
            ).exists()
        )

        self.carteira1.refresh_from_db()

        self.assertEqual(
            self.carteira1.saldo_disponivel,
            Decimal("10.00"),
        )
        self.assertEqual(
            self.carteira1.saldo_reservado,
            Decimal("0.00"),
        )

        movimentacoes_depois = Movimentacao.objects.filter(
            carteira=self.carteira1
        ).count()

        self.assertEqual(
            movimentacoes_depois,
            movimentacoes_antes,
            "Uma tentativa de lance recusada nÃ£o deve gerar movimentaÃ§Ãµes.",
        )

    
    def test_participante_aumenta_o_proprio_lance(self):
        self.client.force_authenticate(user=self.participante1)

        # Primeiro lance: R$ 100,00
        resposta1 = self.client.post(
            self.url,
            {"valor": "100.00"},
            format="json",
        )

        self.assertEqual(resposta1.status_code, 201)

        self.carteira1.refresh_from_db()

        self.assertEqual(
            self.carteira1.saldo_disponivel,
            Decimal("900.00"),
        )
        self.assertEqual(
            self.carteira1.saldo_reservado,
            Decimal("100.00"),
        )

        # Segundo lance do mesmo participante: R$ 150,00
        resposta2 = self.client.post(
            self.url,
            {"valor": "150.00"},
            format="json",
        )

        self.assertEqual(resposta2.status_code, 201)

        # Os dois lances devem continuar no histÃ³rico.
        self.assertEqual(
            Lance.objects.filter(
                leilao=self.leilao,
                participante=self.participante1,
            ).count(),
            2,
        )

        self.assertEqual(
            Decimal(resposta2.data["valor"]),
            Decimal("150.00"),
        )

        # A reserva antiga deve ser substituÃ­da pela nova.
        self.carteira1.refresh_from_db()

        self.assertEqual(
            self.carteira1.saldo_disponivel,
            Decimal("850.00"),
        )
        self.assertEqual(
            self.carteira1.saldo_reservado,
            Decimal("150.00"),
        )
        
    def test_lance_superado_libera_reserva_e_preserva_saldos(self):
        # Participante 1 oferece R$ 100,00.
        self.client.force_authenticate(user=self.participante1)

        resposta1 = self.client.post(
            self.url,
            {"valor": "100.00"},
            format="json",
        )

        self.assertEqual(resposta1.status_code, 201)

        # Participante 2 supera o lance com R$ 150,00.
        self.client.force_authenticate(user=self.participante2)

        resposta2 = self.client.post(
            self.url,
            {"valor": "150.00"},
            format="json",
        )

        self.assertEqual(resposta2.status_code, 201)

        # Os dois lances devem continuar no histÃ³rico.
        lances = Lance.objects.filter(
            leilao=self.leilao
        ).order_by("-valor")

        self.assertEqual(lances.count(), 2)
        self.assertEqual(lances[0].participante, self.participante2)
        self.assertEqual(lances[0].valor, Decimal("150.00"))
        self.assertEqual(lances[1].participante, self.participante1)
        self.assertEqual(lances[1].valor, Decimal("100.00"))

        # Atualiza os dados das carteiras a partir do banco.
        self.carteira1.refresh_from_db()
        self.carteira2.refresh_from_db()

        # Participante 1 recupera os R$ 100,00 reservados.
        self.assertEqual(
            self.carteira1.saldo_disponivel,
            Decimal("1000.00"),
        )
        self.assertEqual(
            self.carteira1.saldo_reservado,
            Decimal("0.00"),
        )

        # Participante 2 fica com R$ 150,00 reservados.
        self.assertEqual(
            self.carteira2.saldo_disponivel,
            Decimal("850.00"),
        )
        self.assertEqual(
            self.carteira2.saldo_reservado,
            Decimal("150.00"),
        )

        # Confere as movimentaÃ§Ãµes financeiras.
        movimentacoes2 = Movimentacao.objects.filter(
            carteira=self.carteira2
        )
        movimentacoes1 = Movimentacao.objects.filter(
            carteira=self.carteira1
        )

        self.assertEqual(
            movimentacoes1.filter(
                tipo=Movimentacao.Tipo.RESERVA
            ).count(),
            1,
        )
        self.assertEqual(
            movimentacoes1.filter(
                tipo=Movimentacao.Tipo.LIBERACAO
            ).count(),
            1,
        )
        self.assertEqual(
            movimentacoes2.filter(
                tipo=Movimentacao.Tipo.RESERVA
            ).count(),
            1,
        )
        self.assertEqual(
            movimentacoes2.filter(
                tipo=Movimentacao.Tipo.LIBERACAO
            ).count(),
            0,
        )


