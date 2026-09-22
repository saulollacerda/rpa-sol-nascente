import { describe, expect, it } from "vitest";
import { ehTerminal, estadoDasEtapas } from "./etapas";
import type { Status } from "../api/tipos";

const estados = (status: Status) => estadoDasEtapas(status).map((e) => e.estado);

describe("etapas da execução", () => {
  it("nomeia as seis etapas do ADR-004 para o gestor", () => {
    expect(estadoDasEtapas("PENDENTE").map((e) => e.rotulo)).toEqual([
      "Na fila",
      "Coletando no BCB",
      "Analisando",
      "Mensagem pronta",
      "Enviando",
      "Enviado",
    ]);
  });

  it("marca as anteriores como feitas e a atual em andamento", () => {
    expect(estados("COLETANDO")).toEqual(["feito", "atual", "pendente", "pendente", "pendente", "pendente"]);
  });

  it("enviado conclui todas", () => {
    expect(estados("ENVIADO")).toEqual(Array(6).fill("feito"));
  });

  it.each([
    ["FALHA_COLETA", ["feito", "falhou", "pendente", "pendente", "pendente", "pendente"]],
    ["FALHA_PROCESSAMENTO", ["feito", "feito", "falhou", "pendente", "pendente", "pendente"]],
    ["FALHA_ENVIO", ["feito", "feito", "feito", "feito", "falhou", "pendente"]],
  ] as const)("%s aponta a etapa que falhou", (status, esperado) => {
    expect(estados(status)).toEqual(esperado);
  });

  it("sem resultado: a análise terminou e o envio não aconteceu, sem ser erro", () => {
    expect(estados("SEM_RESULTADO")).toEqual([
      "feito", "feito", "feito", "interrompido", "interrompido", "interrompido",
    ]);
  });

  it.each([
    ["ENVIADO", true],
    ["SEM_RESULTADO", true],
    ["FALHA_ENVIO", true],
    ["PENDENTE", false],
    ["ENVIANDO", false],
  ] as const)("%s é terminal? %s", (status, esperado) => {
    expect(ehTerminal(status)).toBe(esperado);
  });
});
