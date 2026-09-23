import type { Administradora, Opcoes, Solicitacao } from "../api/tipos";

export interface Formulario {
  dataBase: string;
  segmento: number;
  ufs: string[];
  cnpj: string;
  topConcorrentes: number;
  destinatario: string;
}

// With the chosen administrator, the report tops out at 4: beyond that nobody reads it.
export const MAX_CONCORRENTES = 3;

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
export function validar(f: Formulario, destinatarioObrigatorio = false): Erros {
  const erros: Erros = {};
  if (!f.dataBase) erros.dataBase = "Escolha a data-base";
  if (!f.segmento) erros.segmento = "Escolha o segmento";
  if (f.ufs.length === 0) erros.ufs = "Escolha ao menos uma praça";
  if (!/^\d{1,8}$/.test(f.cnpj)) erros.cnpj = "Escolha a administradora";
  const top = f.topConcorrentes;
  if (!Number.isInteger(top) || top < 0 || top > MAX_CONCORRENTES) {
    erros.topConcorrentes = `Número inteiro entre 0 e ${MAX_CONCORRENTES}`;
  }
  const telefone = validarTelefone(f.destinatario, destinatarioObrigatorio);
  if (telefone) erros.destinatario = telefone;
  return erros;
}

const EXEMPLO = "ex.: 86999990000";

/**
 * Celular brasileiro: DDD + 9 + 8 dígitos. O DDI 55 é opcional; o servidor completa.
 * Vazio só é válido quando o servidor tem um número padrão (WHATSAPP_DESTINATARIO).
 */
export function validarTelefone(valor: string, obrigatorio = false): string | undefined {
  const texto = valor.trim();
  if (!texto)
    return obrigatorio ? "Informe o número de WhatsApp que vai receber o relatório." : undefined;
  if (!/^[\d\s()+.-]+$/.test(texto)) return "Use só números, espaços e ( ) -";

  const digitos = texto.replace(/\D/g, "");
  // Pasted from WhatsApp with the country code: drop it.
  const numero = digitos.length === 13 && digitos.startsWith("55") ? digitos.slice(2) : digitos;
  if (numero.length < 11) return `Número incompleto: DDD + número, ${EXEMPLO}`;
  if (numero.length > 11) return `Número com dígitos demais, ${EXEMPLO}`;
  if (!/^[1-9]{2}$/.test(numero.slice(0, 2))) return "DDD inválido";
  if (numero[2] !== "9") return "Celular começa com 9 depois do DDD";
  return undefined;
}

export const alternarUf = (ufs: string[], uf: string) =>
  ufs.includes(uf) ? ufs.filter((u) => u !== uf) : [...ufs, uf];

export const administradorasDoSegmento = (administradoras: Administradora[], segmento: number) =>
  administradoras.filter((a) => a.segmentos.includes(segmento));
