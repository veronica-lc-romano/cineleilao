
import { useEffect, useState } from "react";
import "./App.css";
import Lances from "./Lances";

const API = "/api";
const API_FILMES = `${API}/filmes/pesquisar/`;
const API_USUARIOS = `${API}/usuarios`;
const API_LEILOES = `${API}/leiloes/`;
const POSTER_URL = "https://image.tmdb.org/t/p/w500";

function mensagemErro(dados, padrao) {
  if (dados?.detail) return dados.detail;
  if (dados?.erro) return dados.erro;
  if (dados?.mensagem) return dados.mensagem;

  if (dados && typeof dados === "object") {
    return Object.entries(dados)
      .map(([campo, valor]) => {
        const texto = Array.isArray(valor) ? valor.join(" ") : String(valor);
        return `${campo}: ${texto}`;
      })
      .join(" ");
  }

  return padrao;
}

function formatarData(data) {
  if (!data) return "Não informada";

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(data));
}

export default function App() {
  // Pesquisa de filmes
  const [termo, setTermo] = useState("");
  const [filmes, setFilmes] = useState([]);
  const [pagina, setPagina] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(0);
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  // Autenticação
  const [usuario, setUsuario] = useState(null);
  const [carregandoAuth, setCarregandoAuth] = useState(true);
  const [modoLogin, setModoLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [senha, setSenha] = useState("");
  const [papel, setPapel] = useState("participante");
  const [email, setEmail] = useState("");
  const [confirmarSenha, setConfirmarSenha] = useState("");
  const [mensagemAuth, setMensagemAuth] = useState("");
  const [erroAuth, setErroAuth] = useState("");
  const [enviandoAuth, setEnviandoAuth] = useState(false);

  // Listagem de leilões
  const [leiloes, setLeiloes] = useState([]);
  const [carregandoLeiloes, setCarregandoLeiloes] = useState(true);
  const [erroLeiloes, setErroLeiloes] = useState("");

  // Criação de leilão
  const [filmeSelecionado, setFilmeSelecionado] = useState("");
  const [lanceInicial, setLanceInicial] = useState("50.00");
  const [inicioEm, setInicioEm] = useState("");
  const [encerraEm, setEncerraEm] = useState("");
  const [descricaoLeilao, setDescricaoLeilao] = useState("");
  const [enviandoLeilao, setEnviandoLeilao] = useState(false);
  const [mensagemLeilao, setMensagemLeilao] = useState("");
  const [erroCriacaoLeilao, setErroCriacaoLeilao] = useState("");

  async function obterCsrf() {
    const resposta = await fetch(`${API_USUARIOS}/csrf/`, {
      credentials: "include",
    });

    const dados = await resposta.json();

    if (!resposta.ok || !dados.csrfToken) {
      throw new Error("Não foi possível obter o token de segurança.");
    }

    return dados.csrfToken;
  }

  async function carregarPerfil() {
    try {
      const resposta = await fetch(`${API_USUARIOS}/me/`, {
        credentials: "include",
      });

      if (resposta.status === 401) {
        setUsuario(null);
        return;
      }

      const dados = await resposta.json();

      if (!resposta.ok) {
        throw new Error(mensagemErro(dados, "Erro ao consultar o perfil."));
      }

      setUsuario(dados.usuario);
    } catch  {
      setErroAuth(
        "Não foi possível verificar a sessão. Confira se o Django está rodando."
      );
    } finally {
      setCarregandoAuth(false);
    }
  }

  async function carregarLeiloes() {
    setCarregandoLeiloes(true);
    setErroLeiloes("");

    try {
      const resposta = await fetch(API_LEILOES);
      const dados = await resposta.json();

      if (!resposta.ok) {
        throw new Error(mensagemErro(dados, "Erro ao carregar leilões."));
      }

      // Compatível com uma lista simples ou uma resposta paginada do DRF.
      setLeiloes(Array.isArray(dados) ? dados : dados.results || []);
    } catch (error) {
      setErroLeiloes(
        error.message === "Failed to fetch"
          ? "Não foi possível conectar ao Django para carregar os leilões."
          : error.message
      );
    } finally {
      setCarregandoLeiloes(false);
    }
  }

    useEffect(() => {
    async function inicializar() {
      await Promise.all([
        carregarPerfil(),
        carregarLeiloes(),
      ]);
    }

    inicializar();
  }, []);

  async function autenticar(event) {
    event.preventDefault();
    setErroAuth("");
    setMensagemAuth("");

    if (!modoLogin && senha !== confirmarSenha) {
      setErroAuth("As senhas não coincidem.");
      return;
    }

    setEnviandoAuth(true);

    try {
      const csrf = await obterCsrf();

      const corpo = modoLogin
        ? {
            username: username.trim(),
            password: senha,
          }
        
        : {
            username: username.trim(),
            email: email.trim(),
            password: senha,
            password_confirm: confirmarSenha,
            papel,
          };


      const resposta = await fetch(
        `${API_USUARIOS}/${modoLogin ? "login" : "cadastro"}/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrf,
          },
          body: JSON.stringify(corpo),
        }
      );

      const dados = await resposta.json();

      if (!resposta.ok) {
        throw new Error(
          mensagemErro(dados, "Não foi possível concluir a operação.")
        );
      }

      setUsuario(dados.usuario);
      setPapel("participante");
      setSenha("");
      setConfirmarSenha("");
      setUsername("");
      setEmail("");
      setMensagemAuth(dados.mensagem || "Operação realizada com sucesso.");
    } catch (error) {
      setErroAuth(
        error.message === "Failed to fetch"
          ? "Não foi possível conectar ao Django. Verifique o backend e o CORS."
          : error.message
      );
    } finally {
      setEnviandoAuth(false);
    }
  }

  async function sair() {
    setErroAuth("");
    setMensagemAuth("");
    setEnviandoAuth(true);

    try {
      const csrf = await obterCsrf();

      const resposta = await fetch(`${API_USUARIOS}/logout/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf,
        },
        body: JSON.stringify({}),
      });

      const dados = await resposta.json();

      if (!resposta.ok) {
        throw new Error(mensagemErro(dados, "Erro ao sair."));
      }

      setUsuario(null);
      setMensagemAuth(dados.mensagem || "Logout realizado com sucesso.");
      setErroCriacaoLeilao("");
      setMensagemLeilao("");
    } catch (error) {
      setErroAuth(error.message);
    } finally {
      setEnviandoAuth(false);
    }
  }

  async function pesquisar(event, novaPagina = 1) {
    event?.preventDefault();

    if (termo.trim().length < 2) {
      setErro("Digite pelo menos 2 caracteres.");
      return;
    }

    setCarregando(true);
    setErro("");

    try {
      const params = new URLSearchParams({
        q: termo.trim(),
        pagina: String(novaPagina),
      });

      const resposta = await fetch(`${API_FILMES}?${params}`);
      const dados = await resposta.json();

      if (!resposta.ok) {
        throw new Error(mensagemErro(dados, "Erro ao pesquisar filmes."));
      }

      setFilmes(dados.resultados || []);
      setPagina(dados.pagina);
      setTotalPaginas(dados.total_paginas);
    } catch (error) {
      setFilmes([]);
      setErro(
        error.message === "Failed to fetch"
          ? "Não foi possível conectar ao Django. Verifique se o backend está rodando."
          : error.message
      );
    } finally {
      setCarregando(false);
    }
  }

  async function criarLeilao(event) {
    event.preventDefault();
    setErroCriacaoLeilao("");
    setMensagemLeilao("");

    const filme = filmes.find(
      (item) => String(item.tmdb_id) === filmeSelecionado
    );

    if (!filme) {
      setErroCriacaoLeilao(
        "Pesquise um filme e selecione-o antes de criar o leilão."
      );
      return;
    }

    if (!inicioEm || !encerraEm) {
      setErroCriacaoLeilao("Informe o início e o encerramento.");
      return;
    }

    const inicio = new Date(inicioEm);
    const encerramento = new Date(encerraEm);

    if (inicio <= new Date()) {
      setErroCriacaoLeilao("O início precisa ser uma data futura.");
      return;
    }

    if (encerramento <= inicio) {
      setErroCriacaoLeilao(
        "O encerramento precisa ser posterior ao início."
      );
      return;
    }

    if (!Number.isFinite(Number(lanceInicial)) || Number(lanceInicial) <= 0) {
      setErroCriacaoLeilao("O lance inicial precisa ser maior que zero.");
      return;
    }

    setEnviandoLeilao(true);

    try {
      const csrf = await obterCsrf();

      const corpo = {
        filme_tmdb_id: Number(filme.tmdb_id),
        titulo: filme.titulo,
        descricao: descricaoLeilao.trim(),
        lance_inicial: Number(lanceInicial).toFixed(2),
        inicio_em: inicio.toISOString(),
        encerra_em: encerramento.toISOString(),
      };

      const resposta = await fetch(API_LEILOES, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf,
        },
        body: JSON.stringify(corpo),
      });

      const dados = await resposta.json();

      if (!resposta.ok) {
        throw new Error(
          mensagemErro(dados, "Não foi possível criar o leilão.")
        );
      }

      setMensagemLeilao(`Leilão "${dados.titulo}" criado com sucesso!`);
      setFilmeSelecionado("");
      setLanceInicial("50.00");
      setInicioEm("");
      setEncerraEm("");
      setDescricaoLeilao("");

      await carregarLeiloes();
    } catch (error) {
      setErroCriacaoLeilao(
        error.message === "Failed to fetch"
          ? "Não foi possível conectar ao Django."
          : error.message
      );
    } finally {
      setEnviandoLeilao(false);
    }
  }

  const ehLeiloeiro = usuario?.papel === "leiloeiro";

  return (
    <main className="container">
      <header className="header">
        <h1>
          Cine<span>Leilão</span>
        </h1>
        <p>Encontre filmes para os próximos leilões.</p>
      </header>

      <section className="auth-panel">
        {carregandoAuth ? (
          <p>Verificando sessão...</p>
        ) : usuario ? (
          <div className="user-bar">
            <div>
              <strong>Olá, {usuario.username}!</strong>
              <p>Perfil: {usuario.papel}</p>
            </div>

            <button type="button" onClick={sair} disabled={enviandoAuth}>
              {enviandoAuth ? "Saindo..." : "Sair"}
            </button>
          </div>
        ) : (
          <>
            <h2>{modoLogin ? "Entrar" : "Criar conta"}</h2>

            <form className="auth-form" onSubmit={autenticar}>
              <label htmlFor="username">Nome de usuário</label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                required
              />

              {!modoLogin && (
                <>
                  <label htmlFor="email">E-mail</label>
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="voce@exemplo.com"
                    required
                  />
                </>
              )}

              
            {!modoLogin && (
              <>
                <label htmlFor="papel">Tipo de conta</label>
                <select
                  id="papel"
                  name="papel"
                  value={papel}
                  onChange={(event) => setPapel(event.target.value)}
                  required
                >
                  <option value="participante">Participante</option>
                  <option value="leiloeiro">Leiloeiro</option>
                </select>
              </>
            )}


              <label htmlFor="senha">Senha</label>
              <input
                id="senha"
                type="password"
                autoComplete={
                  modoLogin ? "current-password" : "new-password"
                }
                value={senha}
                onChange={(event) => setSenha(event.target.value)}
                required
              />

              {!modoLogin && (
                <>
                  <label htmlFor="confirmarSenha">Confirmar senha</label>
                  <input
                    id="confirmarSenha"
                    type="password"
                    autoComplete="new-password"
                    value={confirmarSenha}
                    onChange={(event) =>
                      setConfirmarSenha(event.target.value)
                    }
                    required
                  />
                </>
              )}

              <button type="submit" disabled={enviandoAuth}>
                {enviandoAuth
                  ? "Aguarde..."
                  : modoLogin
                    ? "Entrar"
                    : "Cadastrar"}
              </button>
            </form>

            <button
              type="button"
              className="link-button"
              onClick={() => {
                setModoLogin(!modoLogin);
                setErroAuth("");
                setMensagemAuth("");
              }}
            >
              {modoLogin
                ? "Ainda não tem conta? Cadastre-se"
                : "Já tem conta? Faça login"}
            </button>
          </>
        )}

        {erroAuth && <p className="error">{erroAuth}</p>}
        {mensagemAuth && <p className="success">{mensagemAuth}</p>}
      </section>

      {ehLeiloeiro && (
        <section className="auction-form-panel">
          <h2>Criar leilão</h2>
          <p>
            Pesquise um filme abaixo e selecione-o no formulário para criar
            um leilão.
          </p>

          <form className="auction-form" onSubmit={criarLeilao}>
            <label htmlFor="filmeSelecionado">Filme</label>
            <select
              id="filmeSelecionado"
              value={filmeSelecionado}
              onChange={(event) => setFilmeSelecionado(event.target.value)}
              required
            >
              <option value="">Selecione um filme pesquisado</option>
              {filmes.map((filme) => (
                <option key={filme.tmdb_id} value={filme.tmdb_id}>
                  {filme.titulo}
                </option>
              ))}
            </select>

            <label htmlFor="lanceInicial">Lance inicial (R$)</label>
            <input
              id="lanceInicial"
              type="number"
              min="0.01"
              step="0.01"
              value={lanceInicial}
              onChange={(event) => setLanceInicial(event.target.value)}
              required
            />

            <label htmlFor="inicioEm">Data e hora de início</label>
            <input
              id="inicioEm"
              type="datetime-local"
              value={inicioEm}
              onChange={(event) => setInicioEm(event.target.value)}
              required
            />

            <label htmlFor="encerraEm">Data e hora de encerramento</label>
            <input
              id="encerraEm"
              type="datetime-local"
              value={encerraEm}
              onChange={(event) => setEncerraEm(event.target.value)}
              required
            />

            <label htmlFor="descricaoLeilao">Descrição (opcional)</label>
            <textarea
              id="descricaoLeilao"
              rows="3"
              value={descricaoLeilao}
              onChange={(event) => setDescricaoLeilao(event.target.value)}
              placeholder="Detalhes deste leilão"
            />

            <button type="submit" disabled={enviandoLeilao}>
              {enviandoLeilao ? "Criando..." : "Criar leilão"}
            </button>
          </form>

          {erroCriacaoLeilao && (
            <p className="error">{erroCriacaoLeilao}</p>
          )}
          {mensagemLeilao && (
            <p className="success">{mensagemLeilao}</p>
          )}
        </section>
      )}

      <section className="auctions-section">
        <div className="section-heading">
          <div>
            <h2>Leilões</h2>
            <p>Confira os filmes cadastrados para leilão.</p>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={carregarLeiloes}
            disabled={carregandoLeiloes}
          >
            {carregandoLeiloes ? "Atualizando..." : "Atualizar"}
          </button>
        </div>

        {erroLeiloes && <p className="error">{erroLeiloes}</p>}

        {carregandoLeiloes ? (
          <p>Carregando leilões...</p>
        ) : leiloes.length === 0 ? (
          <p className="empty-state">Ainda não há leilões cadastrados.</p>
        ) : (
          <section className="auction-grid">
            {leiloes.map((leilao) => (

              <article className="auction-card" key={leilao.id}>
                <div className="auction-poster">
                  <span>TMDB #{leilao.filme_tmdb_id}</span>
                </div>

                <div className="auction-info">
                  <h3>{leilao.titulo}</h3>
                      <Lances
                        leilaoId={leilao.id}
                        usuario={usuario}
                        statusLeilao={leilao.status}
                      />

                  <p className={`auction-status ${leilao.status}`}>
                    {leilao.status}
                  </p>


                  <p className="auction-price">
                    Lance inicial:{" "}
                    <strong>
                      {Number(leilao.lance_inicial).toLocaleString("pt-BR", {
                        style: "currency",
                        currency: "BRL",
                      })}
                    </strong>
                  </p>

                  {leilao.descricao && <p>{leilao.descricao}</p>}



                  <p>Início: {formatarData(leilao.inicio_em)}</p>
                  <p>Encerramento: {formatarData(leilao.encerra_em)}</p>
                  <p className="auction-creator">
                    Criado por: {leilao.criado_por_username}
                  </p>
                </div>
              </article>
            ))}
          </section>
        )}
      </section>

      <section className="movie-search-section">
        <h2>Pesquisar filmes</h2>

        <form className="search-form" onSubmit={pesquisar}>
          <input
            type="search"
            value={termo}
            onChange={(event) => setTermo(event.target.value)}
            placeholder="Pesquise por um filme, por exemplo Matrix"
            aria-label="Nome do filme"
          />

          <button type="submit" disabled={carregando}>
            {carregando ? "Pesquisando..." : "Pesquisar"}
          </button>
        </form>

        {erro && <p className="error">{erro}</p>}

        {filmes.length > 0 && (
          <>
            <h2>Filmes encontrados</h2>

            <section className="movie-grid">
              {filmes.map((filme) => (
                <article className="movie-card" key={filme.tmdb_id}>
                  {filme.poster_path ? (
                    <img
                      src={`${POSTER_URL}${filme.poster_path}`}
                      alt={`Pôster de ${filme.titulo}`}
                    />
                  ) : (
                    <div className="no-poster">Pôster indisponível</div>
                  )}

                  <div className="movie-info">
                    <h3>{filme.titulo}</h3>
                    <p>
                      {filme.data_lancamento
                        ? filme.data_lancamento.slice(0, 4)
                        : "Ano não informado"}
                    </p>
                    <p className="synopsis">
                      {filme.sinopse || "Sinopse indisponível."}
                    </p>

                    {ehLeiloeiro && (
                      <button
                        type="button"
                        className="select-movie-button"
                        onClick={() => {
                          setFilmeSelecionado(String(filme.tmdb_id));
                          document
                            .querySelector(".auction-form-panel")
                            ?.scrollIntoView({ behavior: "smooth" });
                        }}
                      >
                        Selecionar para leilão
                      </button>
                    )}
                  </div>
                </article>
              ))}
            </section>

            <nav className="pagination" aria-label="Paginação">
              <button
                onClick={() => pesquisar(null, pagina - 1)}
                disabled={pagina <= 1 || carregando}
                type="button"
              >
                Anterior
              </button>

              <span>
                Página {pagina} de {totalPaginas}
              </span>

              <button
                onClick={() => pesquisar(null, pagina + 1)}
                disabled={pagina >= totalPaginas || carregando}
                type="button"
              >
                Próxima
              </button>
            </nav>
          </>
        )}
      </section>
    </main>
  );
}
