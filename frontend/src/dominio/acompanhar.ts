import type { Execucao } from "../api/tipos";
import { ehTerminal } from "./etapas";

/**
 * Consulta a execução periodicamente até um status final.
 *
 * Polling em vez de WebSocket: a execução leva ~10 s e só um gestor acompanha,
 * então uma consulta por segundo e meio custa nada e dispensa conexão persistente.
 * Devolve a função que cancela.
 */
export function acompanhar(
  id: number,
  buscar: (id: number) => Promise<Execucao>,
  aoAtualizar: (execucao: Execucao) => void,
  intervaloMs = 1500,
): () => void {
  let ativo = true;
  let temporizador: ReturnType<typeof setTimeout> | undefined;

  const ciclo = async () => {
    if (!ativo) return;
    try {
      const execucao = await buscar(id);
      if (!ativo) return;
      aoAtualizar(execucao);
      if (ehTerminal(execucao.status)) return;
    } catch {
      // Falha de rede momentânea: tenta de novo no próximo ciclo.
    }
    if (ativo) temporizador = setTimeout(ciclo, intervaloMs);
  };

  void ciclo();
  return () => {
    ativo = false;
    clearTimeout(temporizador);
  };
}
