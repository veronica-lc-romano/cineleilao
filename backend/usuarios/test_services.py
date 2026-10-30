from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from usuarios.models import Usuario, Carteira, Movimentacao
from usuarios.services import reservar_saldo, liberar_reserva


class ServicosFinanceirosTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="participante_financeiro",
            password="SenhaTeste123!",
            papel=Usuario.Papel.PARTICIPANTE,
        )
        self.carteira = Carteira.objects.create(
            usuario=self.usuario,
            saldo_disponivel=Decimal("500.00"),
            saldo_reservado=Decimal("100.00"),
        )

    def test_reservar_saldo_transfere_valor_e_registra_movimentacao(self):
        reservar_saldo(self.usuario, "75.00")

        self.carteira.refresh_from_db()
        self.assertEqual(self.carteira.saldo_disponivel, Decimal("425.00"))
        self.assertEqual(self.carteira.saldo_reservado, Decimal("175.00"))

        movimento = Movimentacao.objects.get(
            carteira=self.carteira,
            tipo=Movimentacao.Tipo.RESERVA,
        )
        self.assertEqual(movimento.valor, Decimal("75.00"))

    def test_liberar_reserva_transfere_valor_e_registra_movimentacao(self):
        liberar_reserva(self.usuario, "40.00")

        self.carteira.refresh_from_db()
        self.assertEqual(self.carteira.saldo_disponivel, Decimal("540.00"))
        self.assertEqual(self.carteira.saldo_reservado, Decimal("60.00"))

        movimento = Movimentacao.objects.get(
            carteira=self.carteira,
            tipo=Movimentacao.Tipo.LIBERACAO,
        )
        self.assertEqual(movimento.valor, Decimal("40.00"))

    def test_reserva_rejeita_valores_invalidos(self):
        for valor in ("abc", "0", "-1.00", "10.123", "NaN", "Infinity"):
            with self.subTest(valor=valor):
                with self.assertRaises(ValidationError):
                    reservar_saldo(self.usuario, valor)

        self.carteira.refresh_from_db()
        self.assertEqual(self.carteira.saldo_disponivel, Decimal("500.00"))
        self.assertEqual(self.carteira.saldo_reservado, Decimal("100.00"))
        self.assertEqual(Movimentacao.objects.count(), 0)

    def test_liberacao_rejeita_valores_invalidos(self):
        for valor in ("abc", "0", "-1.00", "10.123", "NaN", "Infinity"):
            with self.subTest(valor=valor):
                with self.assertRaises(ValidationError):
                    liberar_reserva(self.usuario, valor)

        self.carteira.refresh_from_db()
        self.assertEqual(self.carteira.saldo_disponivel, Decimal("500.00"))
        self.assertEqual(self.carteira.saldo_reservado, Decimal("100.00"))
        self.assertEqual(Movimentacao.objects.count(), 0)

    def test_reserva_rejeita_saldo_disponivel_insuficiente(self):
        with self.assertRaises(ValidationError):
            reservar_saldo(self.usuario, "600.00")

        self.carteira.refresh_from_db()
        self.assertEqual(self.carteira.saldo_disponivel, Decimal("500.00"))
        self.assertEqual(self.carteira.saldo_reservado, Decimal("100.00"))
        self.assertEqual(Movimentacao.objects.count(), 0)

    def test_liberacao_rejeita_saldo_reservado_insuficiente(self):
        with self.assertRaises(ValidationError):
            liberar_reserva(self.usuario, "150.00")

        self.carteira.refresh_from_db()
        self.assertEqual(self.carteira.saldo_disponivel, Decimal("500.00"))
        self.assertEqual(self.carteira.saldo_reservado, Decimal("100.00"))
        self.assertEqual(Movimentacao.objects.count(), 0)

    def test_falha_ao_registrar_reserva_reverte_alteracoes(self):
        with patch(
            "usuarios.services.Movimentacao.objects.create",
            side_effect=RuntimeError("Falha simulada"),
        ):
            with self.assertRaises(RuntimeError):
                reservar_saldo(self.usuario, "75.00")

        self.carteira.refresh_from_db()
        self.assertEqual(self.carteira.saldo_disponivel, Decimal("500.00"))
        self.assertEqual(self.carteira.saldo_reservado, Decimal("100.00"))
        self.assertEqual(Movimentacao.objects.count(), 0)

    def test_falha_ao_registrar_liberacao_reverte_alteracoes(self):
        with patch(
            "usuarios.services.Movimentacao.objects.create",
            side_effect=RuntimeError("Falha simulada"),
        ):
            with self.assertRaises(RuntimeError):
                liberar_reserva(self.usuario, "40.00")

        self.carteira.refresh_from_db()
        self.assertEqual(self.carteira.saldo_disponivel, Decimal("500.00"))
        self.assertEqual(self.carteira.saldo_reservado, Decimal("100.00"))
        self.assertEqual(Movimentacao.objects.count(), 0)
