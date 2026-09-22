// Dados de exemplo para os testes, com os números reais de referência (CLAUDE.md).
import type { Execucao, Opcoes } from "../api/tipos";

export const OPCOES: Opcoes = {
  data_bases: ["202607", "202606", "202605"],
  data_base_administradoras: "202607",
  administradoras: [
    { cnpj: "45441789", nome: "ADM CONS NAC HONDA LTDA", segmentos: [3, 4] },
    { cnpj: "00000776", nome: "ITAÚ ADM DE CONSÓRCIOS LTDA", segmentos: [1, 4] },
    { cnpj: "11111111", nome: "SÓ IMÓVEIS ADM", segmentos: [1] },
  ],
  segmentos: [
    { codigo: 1, nome: "bens imóveis" },
    { codigo: 4, nome: "motocicletas e motonetas" },
  ],
  ufs: [
    { sigla: "MA", nome: "Maranhão" },
    { sigla: "PI", nome: "Piauí" },
    { sigla: "SP", nome: "São Paulo" },
  ],
  padrao: {
    data_base: "202607",
    segmento: 4,
    ufs: ["PI", "MA"],
    cnpj_administradora: "45441789",
    top_concorrentes: 3,
  },
};

export function execucao(sobrescrever: Partial<Execucao> = {}): Execucao {
  return {
    id: 1,
    status: "ENVIADO",
    tentativas: 1,
    parametros: {
      data_base: "202607",
      segmento: 4,
      ufs: ["MA", "PI"],
      cnpj_administradora: "45441789",
      top_concorrentes: 3,
      destinatario: "5586999990000",
    },
    destinatario: "5586999990000",
    criado_em: "2026-09-22T20:06:02Z",
    atualizado_em: "2026-09-22T20:06:09Z",
    dados_encontrados: {
      data_base_consolidado: "202607",
      data_base_uf: "202606",
      relatorio: {
        segmento: 4,
        pracas: [
          {
            uf: "PI",
            data_base: "202606",
            nome_administradora: "ADM CONS NAC HONDA LTDA",
            ativos_praca: 155648,
            administradoras_na_praca: 40,
            ativos: 148962,
            share: 95.704,
            adesoes_no_trimestre: 19340,
            contemplados_lance_no_trimestre: 9354,
            contemplados_sorteio_no_trimestre: 951,
            concorrentes: [
              { nome_administradora: "BB CONSÓRCIOS", cnpj_raiz: "1", ativos: 2836, share: 1.82 },
            ],
          },
        ],
        nacional: {
          data_base: "202607",
          nome_administradora: "ADM CONS NAC HONDA LTDA",
          cotas_ativas: 2565256,
          cotas_ativas_mercado: 3319425,
          administradoras_no_segmento: 125,
          share: 77.28,
          taxa_administracao: 23.2,
          grupos_ativos: 3760,
          concorrentes: [],
        },
        ufs_sem_resultado: [],
        recorte_uf_indisponivel: false,
      },
    },
    mensagem_gerada: "📊 RADAR DE CONSÓRCIO\nSegmento 4 (motocicletas e motonetas)",
    enviado_em: "2026-09-22T20:06:09Z",
    provider_message_id: "fake-1",
    erro_tipo: null,
    erro_descricao: null,
    ...sobrescrever,
  };
}
