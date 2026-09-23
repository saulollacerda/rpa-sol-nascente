// Contratos da API do backend (app/api/schemas.py e app/api/opcoes.py).

export type Status =
  | "PENDENTE"
  | "COLETANDO"
  | "PROCESSANDO"
  | "MENSAGEM_GERADA"
  | "ENVIANDO"
  | "ENVIADO"
  | "SEM_RESULTADO"
  | "FALHA_COLETA"
  | "FALHA_PROCESSAMENTO"
  | "FALHA_ENVIO";

export type Decisao = "CRIAR" | "REUSAR" | "RETENTAR" | "REENVIAR";

export interface Participacao {
  ativos: number;
  adesoes: number;
  share_carteira: number;
  share_adesoes: number;
}

export interface Recorte {
  ativos: number;
  adesoes: number;
  contemplados_lance: number;
  contemplados_sorteio: number;
  excluidos: number;
  administradoras: number;
}

export interface PosicaoUF {
  uf: string;
  ativos: number;
  adesoes: number;
  alvo: Participacao;
}

/** O BCB não divulga por UF: dados do país inteiro. */
export interface IndicadoresNacionais {
  data_base: string;
  taxa_administracao: number;
  inadimplencia: number;
  contemplacao_mes: number;
  vendas_mes: number;
  credito_pendente: number;
}

export interface PerfilAdministradora {
  cnpj_raiz: string;
  nome_administradora: string;
  recorte: Participacao;
  por_uf: { uf: string; share_carteira: number; share_adesoes: number }[];
  nacional: IndicadoresNacionais | null;
}

export interface Alerta {
  tipo: "ganho" | "perda" | "inadimplencia";
  nome_administradora: string;
  movimentos: { uf: string | null; antes: number; depois: number }[];
  inadimplencia: number | null;
}

export interface Relatorio {
  segmento: number;
  /** Vazio: o recorte é o Brasil inteiro. */
  ufs: string[];
  data_base_uf: string | null;
  data_base_nacional: string | null;
  /** null: não há arquivo por UF até a data-base. */
  recorte: Recorte | null;
  posicoes_uf: PosicaoUF[];
  /** A escolhida vem primeiro. */
  administradoras: PerfilAdministradora[];
  alertas: Alerta[];
}

export interface DadosEncontrados {
  data_base_consolidado: string;
  data_base_uf: string | null;
  /** Execuções anteriores ao template atual guardam outro formato. */
  relatorio: Relatorio | Record<string, unknown>;
}

export interface Parametros {
  data_base: string;
  segmento: number;
  ufs: string[];
  cnpj_administradora: string;
  top_concorrentes: number;
  destinatario: string;
}

export interface Execucao {
  id: number;
  status: Status;
  tentativas: number;
  parametros: Parametros;
  destinatario: string;
  criado_em: string;
  atualizado_em: string;
  dados_encontrados: DadosEncontrados | null;
  mensagem_gerada: string | null;
  enviado_em: string | null;
  provider_message_id: string | null;
  erro_tipo: string | null;
  erro_descricao: string | null;
  /** Execução cujos dados e mensagem foram reaproveitados neste reenvio. */
  origem_id: number | null;
}

export interface Solicitacao {
  data_base: string;
  segmento: number;
  ufs: string[];
  cnpj_administradora: string;
  top_concorrentes: number;
  destinatario?: string;
}

export interface RespostaSolicitacao {
  decisao: Decisao;
  execucao: Execucao;
}

export interface Administradora {
  cnpj: string;
  nome: string;
  segmentos: number[];
}

export interface Opcoes {
  data_bases: string[];
  data_base_administradoras: string;
  administradoras: Administradora[];
  segmentos: { codigo: number; nome: string }[];
  ufs: { sigla: string; nome: string }[];
  padrao: {
    data_base: string | null;
    segmento: number;
    ufs: string[];
    cnpj_administradora: string;
    top_concorrentes: number;
    /** false: o servidor não tem WHATSAPP_DESTINATARIO e o campo é obrigatório. */
    tem_destinatario_padrao: boolean;
  };
}

// app/api/whatsapp.py
export type SituacaoConexao =
  | "CONECTADO"
  | "AGUARDANDO_QR"
  | "INICIANDO"
  | "DESCONECTADO"
  | "INDISPONIVEL";

export interface Conexao {
  situacao: SituacaoConexao;
  conta: string | null;
  /** data URI da imagem; só em AGUARDANDO_QR. */
  qr_code: string | null;
  mensagem: string | null;
}
