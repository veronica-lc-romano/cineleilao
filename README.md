# 🎬 CineLeilão

**Uma plataforma web de leilões de filmes.**

O CineLeilão é uma aplicação web desenvolvida para conectar o universo cinematográfico à dinâmica de leilões online. O projeto permite trabalhar com cadastro de usuários, filmes, leilões e realização de lances.

A aplicação utiliza uma arquitetura separada entre backend e frontend, com comunicação entre as tecnologias e persistência de dados em MariaDB.

## 🚀 Tecnologias utilizadas

| Área | Tecnologias |
|---|---|
| Backend | Python, Django 5.2, Django REST Framework |
| Frontend | React 19, JavaScript, Vite 8 |
| Banco de dados | MariaDB 11 |
| Infraestrutura | Docker e Docker Compose |
| Integração externa | The Movie Database (TMDB) |
| Qualidade | Testes automatizados e ESLint |

## ✨ Funcionalidades

- Cadastro e gerenciamento de usuários.
- Cadastro e consulta de filmes.
- Criação e gerenciamento de leilões.
- Registro e gerenciamento de lances.
- Integração com a API do The Movie Database (TMDB).

## 📁 Estrutura do projeto

```text
cineleilao/
├── backend/
│   ├── config/
│   ├── filmes/
│   ├── lances/
│   ├── leiloes/
│   ├── usuarios/
│   ├── Dockerfile
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   └── assets/
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml
└── .env.example
```

## ⚙️ Requisitos

Antes de começar, instale:

- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Node.js](https://nodejs.org/) e npm
- Uma chave de API do [TMDB](https://www.themoviedb.org/settings/api)

## 🛠️ Instalação e configuração

### 1. Clonar o repositório

```bash
git clone https://github.com/veronica-lc-romano/cineleilao.git
cd cineleilao
```

### 2. Configurar as variáveis de ambiente

Crie seu arquivo `.env` a partir do modelo:

No PowerShell:

```powershell
Copy-Item .env.example .env
```

Configure as variáveis no arquivo `.env`:

| Variável | Descrição |
|---|---|
| `TMDB_API_KEY` | Chave de acesso à API TMDB |
| `DJANGO_SECRET_KEY` | Chave secreta do Django |
| `DJANGO_DEBUG` | Modo de desenvolvimento |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos pelo Django |
| `MARIADB_DATABASE` | Nome do banco de dados |
| `MARIADB_USER` | Usuário do banco |
| `MARIADB_PASSWORD` | Senha do usuário |
| `MARIADB_ROOT_PASSWORD` | Senha administrativa do MariaDB |
| `MARIADB_HOST` | Endereço do banco |
| `MARIADB_PORT` | Porta interna do banco |

Preencha as credenciais localmente. Nunca compartilhe o arquivo `.env`.

### 3. Iniciar banco de dados e backend

Com o Docker Desktop em execução:

```bash
docker compose up -d --build
```

Execute as migrações:

```bash
docker compose exec backend python manage.py migrate
```

Verifique a configuração do Django:

```bash
docker compose exec backend python manage.py check
```

Backend:

http://localhost:8000

### 4. Iniciar o frontend

Abra outro terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

http://localhost:5173

## 🧪 Testes e validações

### Backend

Executar os testes automatizados:

```bash
docker compose exec backend python manage.py test
```

Verificar a configuração:

```bash
docker compose exec backend python manage.py check
```

### Frontend

Executar o ESLint:

```bash
cd frontend
npm run lint
```

Gerar a versão de produção:

```bash
npm run build
```

## 🔐 Segurança

- Credenciais devem ser armazenadas em variáveis de ambiente.
- O arquivo `.env` não deve ser versionado.
- Backups de banco de dados não devem ser publicados.
- Chaves de APIs e senhas não devem ser incluídas no código-fonte.
- Utilize configurações adequadas para produção antes de disponibilizar a aplicação publicamente.

## 📌 Status do projeto

Projeto em desenvolvimento, com foco em aprendizado, aplicação de boas práticas e construção de uma plataforma web utilizando tecnologias modernas.

## 👩‍💻 Desenvolvedora

**Veronica Romano**

Projeto desenvolvido como parte do portfólio de desenvolvimento de software.

---

*Tecnologias, arquitetura e funcionalidades documentadas com base na estrutura atual do projeto.*
