import { describe, expect, it } from "vitest";
import {
  administradorasDoSegmento,
  alternarUf,
  estadoInicial,
  montarSolicitacao,
  validar,
} from "./formulario";
import type { Opcoes } from "../api/tipos";

const PADRAO: Opcoes["padrao"] = {
  data_base: "202607",
  segmento: 4,
  ufs: ["PI", "MA"],
  cnpj_administradora: "45441789",
  top_concorrentes: 3,
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
    [{ ufs: [] }, "ufs"],
    [{ dataBase: "" }, "dataBase"],
    [{ destinatario: "123" }, "destinatario"],
    [{ cnpj: "" }, "cnpj"],
  ])("recusa %o", (alteracao, campo) => {
    expect(validar({ ...estadoInicial(PADRAO), ...alteracao })).toHaveProperty(campo);
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
