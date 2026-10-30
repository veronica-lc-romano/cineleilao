import json

from django.test import Client, TestCase
from django.urls import reverse

from .models import Carteira, Usuario


class AutenticacaoTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            username="participante_teste",
            email="participante@example.com",
            password="SenhaSegura!2026",
            papel=Usuario.Papel.PARTICIPANTE,
        )

        self.cadastro_url = reverse("cadastro")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.perfil_url = reverse("perfil")
        self.csrf_url = reverse("csrf-token")

    def post_json(self, url, dados):
        return self.client.post(
            url,
            data=json.dumps(dados),
            content_type="application/json",
        )

    def dados_cadastro(self, **sobrescritos):
        dados = {
            "username": "novo_participante",
            "email": "novo@example.com",
            "password": "OutraSenhaForte!2026",
            "password_confirm": "OutraSenhaForte!2026",
        }
        dados.update(sobrescritos)
        return dados

    # Cadastro

    def test_cadastro_cria_usuario_e_carteira(self):
        resposta = self.post_json(
            self.cadastro_url,
            self.dados_cadastro(),
        )

        self.assertEqual(resposta.status_code, 201)

        usuario = Usuario.objects.get(username="novo_participante")
        self.assertEqual(usuario.email, "novo@example.com")
        self.assertEqual(
            usuario.papel,
            Usuario.Papel.PARTICIPANTE,
        )
        self.assertTrue(
            usuario.check_password("OutraSenhaForte!2026")
        )
        self.assertTrue(
            Carteira.objects.filter(usuario=usuario).exists()
        )
        self.assertEqual(
            resposta.json()["usuario"]["username"],
            "novo_participante",
        )

    def test_cadastro_com_json_invalido_retorna_400(self):
        resposta = self.client.post(
            self.cadastro_url,
            data="{json invalido",
            content_type="application/json",
        )

        self.assertEqual(resposta.status_code, 400)

    def test_cadastro_sem_campos_obrigatorios_retorna_400(self):
        resposta = self.post_json(
            self.cadastro_url,
            {
                "username": "",
                "email": "",
                "password": "",
            },
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertFalse(
            Usuario.objects.filter(username="").exists()
        )

    def test_cadastro_com_senhas_diferentes_retorna_400(self):
        resposta = self.post_json(
            self.cadastro_url,
            self.dados_cadastro(
                password="SenhaForte!2026",
                password_confirm="SenhaDiferente!2026",
            ),
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertFalse(
            Usuario.objects.filter(
                username="novo_participante"
            ).exists()
        )

    def test_cadastro_com_username_duplicado_retorna_400(self):
        resposta = self.post_json(
            self.cadastro_url,
            self.dados_cadastro(username="PARTICIPANTE_TESTE"),
        )

        self.assertEqual(resposta.status_code, 400)

    def test_cadastro_com_email_duplicado_retorna_400(self):
        resposta = self.post_json(
            self.cadastro_url,
            self.dados_cadastro(email="PARTICIPANTE@example.com"),
        )

        self.assertEqual(resposta.status_code, 400)

    def test_cadastro_com_senha_fraca_retorna_400(self):
        resposta = self.post_json(
            self.cadastro_url,
            self.dados_cadastro(
                password="123",
                password_confirm="123",
            ),
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertFalse(
            Usuario.objects.filter(
                username="novo_participante"
            ).exists()
        )

    # Login

    def test_login_com_credenciais_validas(self):
        resposta = self.post_json(
            self.login_url,
            {
                "username": "participante_teste",
                "password": "SenhaSegura!2026",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.json()["usuario"]["username"],
            "participante_teste",
        )

    def test_login_com_senha_incorreta_retorna_401(self):
        resposta = self.post_json(
            self.login_url,
            {
                "username": "participante_teste",
                "password": "SenhaErrada!2026",
            },
        )

        self.assertEqual(resposta.status_code, 401)

    def test_login_com_usuario_inexistente_retorna_401(self):
        resposta = self.post_json(
            self.login_url,
            {
                "username": "nao_existe",
                "password": "SenhaSegura!2026",
            },
        )

        self.assertEqual(resposta.status_code, 401)

    def test_login_sem_campos_obrigatorios_retorna_400(self):
        resposta = self.post_json(
            self.login_url,
            {
                "username": "",
                "password": "",
            },
        )

        self.assertEqual(resposta.status_code, 400)

    # Perfil e sessão

    def test_perfil_sem_autenticacao_retorna_401(self):
        resposta = self.client.get(self.perfil_url)

        self.assertEqual(resposta.status_code, 401)

    def test_perfil_autenticado_retorna_dados_do_usuario(self):
        self.client.force_login(self.usuario)

        resposta = self.client.get(self.perfil_url)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.json()["usuario"]["username"],
            "participante_teste",
        )
        self.assertEqual(
            resposta.json()["usuario"]["email"],
            "participante@example.com",
        )

    def test_logout_encerra_sessao(self):
        self.client.force_login(self.usuario)

        resposta_logout = self.client.post(self.logout_url)

        self.assertEqual(resposta_logout.status_code, 200)

        resposta_perfil = self.client.get(self.perfil_url)
        self.assertEqual(resposta_perfil.status_code, 401)

    # Proteção CSRF

    def test_cadastro_sem_csrf_retorna_403(self):
        cliente = Client(enforce_csrf_checks=True)

        resposta = cliente.post(
            self.cadastro_url,
            data=json.dumps(self.dados_cadastro()),
            content_type="application/json",
        )

        self.assertEqual(resposta.status_code, 403)

    def test_login_sem_csrf_retorna_403(self):
        cliente = Client(enforce_csrf_checks=True)

        resposta = cliente.post(
            self.login_url,
            data=json.dumps({
                "username": "participante_teste",
                "password": "SenhaSegura!2026",
            }),
            content_type="application/json",
        )

        self.assertEqual(resposta.status_code, 403)

    def test_logout_sem_csrf_retorna_403(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)

        resposta = cliente.post(self.logout_url)

        self.assertEqual(resposta.status_code, 403)

    def test_csrf_com_token_valido_permite_cadastro(self):
        cliente = Client(enforce_csrf_checks=True)

        resposta_token = cliente.get(self.csrf_url)
        self.assertEqual(resposta_token.status_code, 200)

        token = resposta_token.json()["csrfToken"]

        resposta = cliente.post(
            self.cadastro_url,
            data=json.dumps(self.dados_cadastro()),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(resposta.status_code, 201)

    def test_endpoint_csrf_retorna_token_e_cookie(self):
        cliente = Client(enforce_csrf_checks=True)

        resposta = cliente.get(self.csrf_url)

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("csrfToken", resposta.json())
        self.assertIn("csrftoken", cliente.cookies)
