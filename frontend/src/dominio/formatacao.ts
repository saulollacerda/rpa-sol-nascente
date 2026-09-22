import type { Status } from "../api/tipos";

const MESES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

/** '202607' → 'Julho/2026'. Formato inesperado volta como veio. */
export function rotuloDataBase(dataBase: string): string {
  const casamento = /^(\d{4})(\d{2})$/.exec(dataBase);
  const mes = casamento ? Number(casamento[2]) : 0;
  return casamento && mes >= 1 && mes <= 12 ? `${MESES[mes - 1]}/${casamento[1]}` : dataBase;
}

// As praças da Sol Nascente (PI e MA) ficam em UTC-3, sem horário de verão.
const FUSO = "America/Fortaleza";

const formatoDataHora = new Intl.DateTimeFormat("pt-BR", {
  timeZone: FUSO,
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

export function dataHora(iso: string): string {
  const p = Object.fromEntries(formatoDataHora.formatToParts(new Date(iso)).map((x) => [x.type, x.value]));
  return `${p.day}/${p.month}/${p.year} ${p.hour}:${p.minute}`;
}

export function telefone(digitos: string): string {
  const casamento = /^55(\d{2})(\d{4,5})(\d{4})$/.exec(digitos);
  return casamento ? `+55 ${casamento[1]} ${casamento[2]}-${casamento[3]}` : digitos;
}

const numero = new Intl.NumberFormat("pt-BR");
export const inteiro = (valor: number) => numero.format(valor);
export const percentual = (valor: number) => `${valor.toFixed(1).replace(".", ",")}%`;

export type Tom = "sucesso" | "erro" | "neutro" | "andamento";

const STATUS: Record<Status, { rotulo: string; tom: Tom }> = {
  PENDENTE: { rotulo: "Na fila", tom: "andamento" },
  COLETANDO: { rotulo: "Coletando", tom: "andamento" },
  PROCESSANDO: { rotulo: "Analisando", tom: "andamento" },
  MENSAGEM_GERADA: { rotulo: "Mensagem pronta", tom: "andamento" },
  ENVIANDO: { rotulo: "Enviando", tom: "andamento" },
  ENVIADO: { rotulo: "Enviado", tom: "sucesso" },
  SEM_RESULTADO: { rotulo: "Sem resultado", tom: "neutro" },
  FALHA_COLETA: { rotulo: "Falha na coleta", tom: "erro" },
  FALHA_PROCESSAMENTO: { rotulo: "Falha na análise", tom: "erro" },
  FALHA_ENVIO: { rotulo: "Falha no envio", tom: "erro" },
};

export const rotuloStatus = (status: Status) => STATUS[status];

const UFS: Record<string, string> = {
  AC: "Acre", AL: "Alagoas", AP: "Amapá", AM: "Amazonas", BA: "Bahia", CE: "Ceará",
  DF: "Distrito Federal", ES: "Espírito Santo", GO: "Goiás", MA: "Maranhão",
  MT: "Mato Grosso", MS: "Mato Grosso do Sul", MG: "Minas Gerais", PA: "Pará",
  PB: "Paraíba", PR: "Paraná", PE: "Pernambuco", PI: "Piauí", RJ: "Rio de Janeiro",
  RN: "Rio Grande do Norte", RS: "Rio Grande do Sul", RO: "Rondônia", RR: "Roraima",
  SC: "Santa Catarina", SP: "São Paulo", SE: "Sergipe", TO: "Tocantins",
};

export const nomeUf = (sigla: string) => UFS[sigla] ?? sigla;
