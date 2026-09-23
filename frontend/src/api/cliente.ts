import type { Conexao, Execucao, Opcoes, RespostaSolicitacao, Solicitacao } from "./tipos";

export class ErroApi extends Error {
  constructor(
    public readonly status: number,
    mensagem: string,
  ) {
    super(mensagem);
    this.name = "ErroApi";
  }
}

interface ErroDeValidacao {
  loc: (string | number)[];
  msg: string;
}

/** Traduz o corpo de erro do FastAPI em uma frase para a tela. */
export function mensagemDeErro(status: number, corpo: unknown): string {
  const detalhe = (corpo as { detail?: unknown } | null)?.detail;
  if (typeof detalhe === "string") return detalhe;
  if (Array.isArray(detalhe)) {
    return (detalhe as ErroDeValidacao[])
      .map((d) => {
        const campo = d.loc.filter((parte) => parte !== "body").join(".");
        const texto = d.msg.replace(/^Value error, /, "");
        return campo ? `${campo}: ${texto}` : texto;
      })
      .join("; ");
  }
  return `erro inesperado (HTTP ${status})`;
}

async function pedir<T>(url: string, init?: RequestInit): Promise<T> {
  let resposta: Response;
  try {
    resposta = await fetch(url, init);
  } catch {
    throw new ErroApi(0, "sem conexão com o servidor");
  }
  const NAO_JSON = Symbol();
  const corpo: unknown = await resposta.json().catch(() => NAO_JSON);
  if (!resposta.ok) {
    const detalhe = corpo === NAO_JSON ? null : corpo;
    throw new ErroApi(resposta.status, mensagemDeErro(resposta.status, detalhe));
  }
  // 200 com HTML: quem respondeu não foi a API (ex.: proxy do Vite sem a rota).
  if (corpo === NAO_JSON) throw new ErroApi(resposta.status, "resposta inesperada do servidor");
  return corpo as T;
}

export const obterOpcoes = () => pedir<Opcoes>("/opcoes");

export const solicitar = (solicitacao: Solicitacao) =>
  pedir<RespostaSolicitacao>("/execucoes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(solicitacao),
  });

export const obterExecucao = (id: number) => pedir<Execucao>(`/execucoes/${id}`);

export const listarExecucoes = (limite = 20) => pedir<Execucao[]>(`/execucoes?limite=${limite}`);

export const obterConexao = () => pedir<Conexao>("/whatsapp/conexao");

export const reconectarWhatsApp = () =>
  pedir<null>("/whatsapp/conexao/reconectar", { method: "POST" });
