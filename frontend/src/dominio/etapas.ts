import type { Status } from "../api/tipos";

export type EstadoDaEtapa = "feito" | "atual" | "pendente" | "falhou" | "interrompido";

export interface Etapa {
  rotulo: string;
  estado: EstadoDaEtapa;
}

// Caminho feliz da máquina de estados do ADR-004.
const CAMINHO: { status: Status; rotulo: string }[] = [
  { status: "PENDENTE", rotulo: "Na fila" },
  { status: "COLETANDO", rotulo: "Coletando no BCB" },
  { status: "PROCESSANDO", rotulo: "Analisando" },
  { status: "MENSAGEM_GERADA", rotulo: "Mensagem pronta" },
  { status: "ENVIANDO", rotulo: "Enviando" },
  { status: "ENVIADO", rotulo: "Enviado" },
];

// Em que etapa cada desfecho fora do caminho feliz aconteceu.
const DESVIOS: Partial<Record<Status, { indice: number; estado: EstadoDaEtapa }>> = {
  FALHA_COLETA: { indice: 1, estado: "falhou" },
  FALHA_PROCESSAMENTO: { indice: 2, estado: "falhou" },
  FALHA_ENVIO: { indice: 4, estado: "falhou" },
};

const TERMINAIS: ReadonlySet<Status> = new Set([
  "ENVIADO",
  "SEM_RESULTADO",
  "FALHA_COLETA",
  "FALHA_PROCESSAMENTO",
  "FALHA_ENVIO",
]);

export const ehTerminal = (status: Status) => TERMINAIS.has(status);

export function estadoDasEtapas(status: Status): Etapa[] {
  if (status === "ENVIADO") return CAMINHO.map(({ rotulo }) => ({ rotulo, estado: "feito" }));

  if (status === "SEM_RESULTADO") {
    // A análise concluiu que não há o que enviar: não é erro, o fluxo só para.
    return CAMINHO.map(({ rotulo }, i) => ({ rotulo, estado: i <= 2 ? "feito" : "interrompido" }));
  }

  const desvio = DESVIOS[status];
  const atual = desvio?.indice ?? CAMINHO.findIndex((e) => e.status === status);
  return CAMINHO.map(({ rotulo }, i) => ({
    rotulo,
    estado: i < atual ? "feito" : i === atual ? (desvio?.estado ?? "atual") : "pendente",
  }));
}
