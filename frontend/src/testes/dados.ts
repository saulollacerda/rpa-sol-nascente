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
    tem_destinatario_padrao: true,
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
        ufs: ["MA", "PI"],
        data_base_uf: "202606",
        data_base_nacional: "202607",
        recorte: {
          ativos: 750,
          adesoes: 200,
          contemplados_lance: 900,
          contemplados_sorteio: 100,
          excluidos: 250,
          administradoras: 46,
        },
        posicoes_uf: [
          {
            uf: "MA",
            ativos: 249533,
            adesoes: 29664,
            alvo: { ativos: 228238, adesoes: 27261, share_carteira: 91.46, share_adesoes: 91.9 },
          },
          {
            uf: "PI",
            ativos: 155648,
            adesoes: 20011,
            alvo: { ativos: 148962, adesoes: 19340, share_carteira: 95.7, share_adesoes: 96.64 },
          },
        ],
        administradoras: [
          {
            cnpj_raiz: "45441789",
            nome_administradora: "ADM CONS NAC HONDA LTDA",
            recorte: {
              ativos: 377200,
              adesoes: 46601,
              share_carteira: 93.09,
              share_adesoes: 93.81,
            },
            por_uf: [],
            nacional: {
              data_base: "202607",
              taxa_administracao: 23.18,
              inadimplencia: 10.6,
              contemplacao_mes: 4.3,
              vendas_mes: 105315,
              credito_pendente: 142436,
            },
          },
          {
            cnpj_raiz: "47458153",
            nome_administradora: "YAMAHA ADM CONS LTDA",
            recorte: { ativos: 9700, adesoes: 898, share_carteira: 2.4, share_adesoes: 1.8 },
            por_uf: [],
            nacional: null,
          },
        ],
        alertas: [
          {
            tipo: "inadimplencia",
            nome_administradora: "YAMAHA ADM CONS LTDA",
            movimentos: [],
            inadimplencia: 18.5,
          },
        ],
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
