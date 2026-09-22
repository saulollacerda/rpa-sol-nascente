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

export type Decisao = "CRIAR" | "REUSAR" | "RETENTAR";

export interface Concorrente {
  nome_administradora: string;
  cnpj_raiz: string;
  ativos: number;
  share: number;
}

export interface Praca {
  uf: string;
  data_base: string;
  nome_administradora: string;
  ativos_praca: number;
  administradoras_na_praca: number;
  ativos: number;
  share: number;
  adesoes_no_trimestre: number;
  contemplados_lance_no_trimestre: number;
  contemplados_sorteio_no_trimestre: number;
  concorrentes: Concorrente[];
}

export interface Nacional {
  data_base: string;
  nome_administradora: string;
  cotas_ativas: number;
  cotas_ativas_mercado: number;
  administradoras_no_segmento: number;
  share: number;
  taxa_administracao: number;
  grupos_ativos: number;
  concorrentes: Concorrente[];
}

export interface DadosEncontrados {
  data_base_consolidado: string;
  data_base_uf: string | null;
  relatorio: {
    segmento: number;
    pracas: Praca[];
    nacional: Nacional | null;
    ufs_sem_resultado: string[];
    recorte_uf_indisponivel: boolean;
  };
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
  };
}
