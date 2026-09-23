import { describe, expect, it } from "vitest";
import {
  administradorasDoSegmento,
  alternarUf,
  estadoInicial,
  montarSolicitacao,
  validar,
  validarTelefone,
} from "./formulario";
import type { Opcoes } from "../api/tipos";

const PADRAO: Opcoes["padrao"] = {
  data_base: "202607",
  segmento: 4,
  ufs: ["PI", "MA"],
  cnpj_administradora: "45441789",
  top_concorrentes: 3,
  tem_destinatario_padrao: true,
};

describe("formulário do painel", () => {
  it("começa com os padrões da Sol Nascente Motos", () => {
    expect(estadoInicial(PADRAO)).toEqual({
      dataBase: "202607",
      segmento: 4,
      ufs: ["PI", "MA"],
      cnpj: "45441789",
      topConcorrentes: 3,
      destinatario: "",
    });
  });

  it("monta o corpo esperado pela API", () => {
    const form = { ...estadoInicial(PADRAO), destinatario: " +55 86 99999-0000 " };
    expect(montarSolicitacao(form)).toEqual({
      data_base: "202607",
      segmento: 4,
      ufs: ["PI", "MA"],
      cnpj_administradora: "45441789",
      top_concorrentes: 3,
      destinatario: "+55 86 99999-0000",
    });
  });

  it("sem destinatário, o campo não vai e o servidor usa o do .env", () => {
    expect(montarSolicitacao(estadoInicial(PADRAO))).not.toHaveProperty("destinatario");
  });

  it("formulário padrão é válido", () => {
    expect(validar(estadoInicial(PADRAO))).toEqual({});
  });

  it.each([
    [{ topConcorrentes: 4 }, "topConcorrentes"],
    [{ ufs: [] }, "ufs"],
    [{ segmento: 0 }, "segmento"],
    [{ dataBase: "" }, "dataBase"],
    [{ destinatario: "123" }, "destinatario"],
    [{ cnpj: "" }, "cnpj"],
  ])("recusa %o", (alteracao, campo) => {
    expect(validar({ ...estadoInicial(PADRAO), ...alteracao })).toHaveProperty(campo);
  });

  it("recusa concorrentes fracionado", () => {
    expect(validar({ ...estadoInicial(PADRAO), topConcorrentes: 1.5 })).toHaveProperty(
      "topConcorrentes",
    );
  });

  describe("telefone do destinatário", () => {
    it("sem número padrão no servidor, o campo é obrigatório", () => {
      expect(validarTelefone("", true)).toBe(
        "Informe o número de WhatsApp que vai receber o relatório.",
      );
      expect(validar(estadoInicial(PADRAO), true)).toHaveProperty("destinatario");
    });

    it.each(["", "86999990000", "(86) 99999-0000", "86 99999 0000", "+55 86 99999-0000"])(
      "aceita %j",
      (valor) => {
        expect(validarTelefone(valor)).toBeUndefined();
      },
    );

    it.each([
      ["86 9889A-6964", /só números/i],
      ["8698892696", /incompleto/i],
      ["869999900000", /dígitos demais/i],
      ["06999990000", /DDD/],
      ["86899990000", /começa com 9/],
    ])("recusa %j", (valor, mensagem) => {
      expect(validarTelefone(valor)).toMatch(mensagem);
    });
  });

  it("alterna uma UF", () => {
    expect(alternarUf(["PI", "MA"], "SP")).toEqual(["PI", "MA", "SP"]);
    expect(alternarUf(["PI", "MA"], "PI")).toEqual(["MA"]);
  });

  it("lista só administradoras que atuam no segmento", () => {
    const adms = [
      { cnpj: "1", nome: "A", segmentos: [1, 4] },
      { cnpj: "2", nome: "B", segmentos: [1] },
    ];
    expect(administradorasDoSegmento(adms, 4).map((a) => a.cnpj)).toEqual(["1"]);
  });
});
