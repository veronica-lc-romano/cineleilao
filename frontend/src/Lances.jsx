
import { useCallback, useEffect, useState } from "react";

const API = "/api";

export default function Lances({ leilaoId, usuario }) {
  const [lances, setLances] = useState([]);
  const [valor, setValor] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState("");
  const [mensagem, setMensagem] = useState("");

  const carregarLances = useCallback(async () => {
    try {
      const resposta = await fetch(
        `${API}/leiloes/${leilaoId}/lances/`
      );

      if (!resposta.ok) {
        throw new Error("Não foi possível carregar os lances.");
      }

      setLances(await resposta.json());
    } catch (e) {
      setErro(e.message);
    }
  }, [leilaoId]);

    useEffect(() => {
    async function inicializar() {
      await carregarLances();
    }

    inicializar();
  }, [carregarLances]);

  async function enviarLance(e) {
    e.preventDefault();
    setErro("");
    setMensagem("");
    setCarregando(true);

    try {
      if (!usuario) {
        throw new Error("Entre na sua conta para dar um lance.");
      }

      const respostaCsrf = await fetch(`${API}/usuarios/csrf/`, {
        credentials: "include",
      });

      const dadosCsrf = await respostaCsrf.json();

      const resposta = await fetch(
        `${API}/leiloes/${leilaoId}/lances/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": dadosCsrf.csrfToken,
          },
          body: JSON.stringify({ valor }),
        }
      );

      const dados = await resposta.json();

      if (!resposta.ok) {
        const detalhe = dados.detail;
        const erroValor = Array.isArray(dados.valor)
          ? dados.valor.join(" ")
          : dados.valor;

        throw new Error(
          erroValor || detalhe || "Não foi possível registrar o lance."
        );
      }

      setMensagem("Lance registrado com sucesso!");
      setValor("");
      await carregarLances();
    } catch (e) {
      setErro(e.message);
    } finally {
      setCarregando(false);
    }
  }

  const maiorLance = lances.length
    ? lances.reduce((maior, lance) =>
        Number(lance.valor) > Number(maior.valor) ? lance : maior
      )
    : null;

  return (
    <section className="lances-container">
      <h3>Lances do leilão</h3>

      <p>
        <strong>Maior lance:</strong>{" "}
        {maiorLance
          ? `R$ ${Number(maiorLance.valor).toFixed(2)}`
          : "Nenhum lance registrado"}
      </p>

      {erro && <p className="text-danger">{erro}</p>}
      {mensagem && <p className="text-success">{mensagem}</p>}

      {usuario?.papel === "participante" && (
        <form onSubmit={enviarLance}>
          <label htmlFor={`valor-lance-${leilaoId}`}>
            Seu lance (R$)
          </label>

          <input
            id={`valor-lance-${leilaoId}`}
            className="form-control"
            type="number"
            min="0.01"
            step="0.01"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            placeholder="Ex.: 75.00"
            required
          />

          <button
            className="btn btn-primary mt-2"
            type="submit"
            disabled={carregando}
          >
            {carregando ? "Enviando..." : "Dar lance"}
          </button>
        </form>
      )}

      <ul className="list-group mt-3">
        {lances.map((lance) => (
          <li className="list-group-item" key={lance.id}>
            <strong>
              R$ {Number(lance.valor).toFixed(2)}
            </strong>
            {" — "}
            {lance.participante_username}
            <small className="d-block text-muted">
              {new Date(lance.criado_em).toLocaleString("pt-BR")}
            </small>
          </li>
        ))}
      </ul>
    </section>
  );
}
