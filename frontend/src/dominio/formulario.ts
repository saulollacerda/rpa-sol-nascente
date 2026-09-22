import type { Administradora, Opcoes, Solicitacao } from "../api/tipos";

export interface Formulario {
  dataBase: string;
  segmento: number;
  ufs: string[];
  cnpj: string;
  topConcorrentes: number;
  destinatario: string;
}

export type Erros = Partial<Record<keyof Formulario, string>>;

export function estadoInicial(padrao: Opcoes["padrao"]): Formulario {
  return {
    dataBase: padrao.data_base ?? "",
    segmento: padrao.segmento,
    ufs: [...padrao.ufs],
    cnpj: padrao.cnpj_administradora,
    topConcorrentes: padrao.top_concorrentes,
    destinatario: "",
  };
}

export function montarSolicitacao(f: Formulario): Solicitacao {
  const destinatario = f.destinatario.trim();
  return {
    data_base: f.dataBase,
    segmento: f.segmento,
    ufs: f.ufs,
    cnpj_administradora: f.cnpj,
    top_concorrentes: f.topConcorrentes,
    // Vazio: o servidor usa o WHATSAPP_DESTINATARIO do .env.
    ...(destinatario ? { destinatario } : {}),
  };
}

/** Espelha as regras do backend para avisar antes de enviar; o backend continua validando. */
export function validar(f: Formulario): Erros {
  const erros: Erros = {};
  if (!f.dataBase) erros.dataBase = "Escolha a data-base";
  if (f.ufs.length === 0) erros.ufs = "Escolha ao menos uma UF";
  if (!/^\d{1,8}$/.test(f.cnpj)) erros.cnpj = "Escolha a administradora";
  if (f.topConcorrentes < 0 || f.topConcorrentes > 10) erros.topConcorrentes = "Entre 0 e 10";
  const digitos = f.destinatario.replace(/\D/g, "");
  if (f.destinatario.trim() && (digitos.length < 10 || digitos.length > 15)) {
    erros.destinatario = "Telefone com DDI e DDD, ex.: +55 86 99999-0000";
  }
  return erros;
}

export const alternarUf = (ufs: string[], uf: string) =>
  ufs.includes(uf) ? ufs.filter((u) => u !== uf) : [...ufs, uf];

export const administradorasDoSegmento = (administradoras: Administradora[], segmento: number) =>
  administradoras.filter((a) => a.segmentos.includes(segmento));
