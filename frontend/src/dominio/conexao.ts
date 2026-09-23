import { ErroApi } from "../api/cliente";
import type { Conexao, SituacaoConexao } from "../api/tipos";
import type { Tom } from "./formatacao";

interface Intervalos {
  /** Enquanto não conecta: o QR code vence em cerca de um minuto. */
  rapidoMs: number;
  /** Conectado: só para notar se o celular desconectar. */
  lentoMs: number;
}

/**
 * Consulta a conexão do WhatsApp sem parar, no ritmo da situação.
 *
 * Ao contrário de `acompanhar`, não há status final: uma sessão conectada pode
 * cair a qualquer momento. Devolve a função que cancela.
 */
export function vigiarConexao(
  buscar: () => Promise<Conexao>,
  aoAtualizar: (conexao: Conexao) => void,
  { rapidoMs, lentoMs }: Intervalos = { rapidoMs: 3000, lentoMs: 15_000 },
): () => void {
  let ativo = true;
  let temporizador: ReturnType<typeof setTimeout> | undefined;

  const ciclo = async () => {
    let conexao: Conexao;
    try {
      conexao = await buscar();
    } catch (erro) {
      conexao = {
        situacao: "INDISPONIVEL",
        conta: null,
        qr_code: null,
        mensagem: erro instanceof ErroApi ? erro.message : "sem conexão com o servidor",
      };
    }
    if (!ativo) return;
    aoAtualizar(conexao);
    temporizador = setTimeout(ciclo, conexao.situacao === "CONECTADO" ? lentoMs : rapidoMs);
  };

  void ciclo();
  return () => {
    ativo = false;
    clearTimeout(temporizador);
  };
}

const SITUACAO: Record<SituacaoConexao, { rotulo: string; tom: Tom }> = {
  CONECTADO: { rotulo: "Conectado", tom: "sucesso" },
  AGUARDANDO_QR: { rotulo: "Aguardando leitura", tom: "andamento" },
  INICIANDO: { rotulo: "Iniciando", tom: "andamento" },
  DESCONECTADO: { rotulo: "Desconectado", tom: "erro" },
  INDISPONIVEL: { rotulo: "Indisponível", tom: "erro" },
};

export const rotuloConexao = (situacao: SituacaoConexao) => SITUACAO[situacao];
