import { describe, expect, it } from "vitest";
import { dataHora, nomeUf, rotuloDataBase, rotuloStatus, telefone } from "./formatacao";

describe("formatação", () => {
  it.each([
    ["202607", "Julho/2026"],
    ["202612", "Dezembro/2026"],
    ["2026-07", "2026-07"],
    ["202613", "202613"],
  ])("data-base %s → %s", (entrada, esperado) => {
    expect(rotuloDataBase(entrada)).toBe(esperado);
  });

  it("data e hora no fuso das praças (UTC-3, sem horário de verão)", () => {
    expect(dataHora("2026-09-22T20:06:09Z")).toBe("22/09/2026 17:06");
  });

  it("telefone brasileiro legível", () => {
    expect(telefone("5586999990000")).toBe("+55 86 99999-0000");
  });

  it("telefone fora do padrão volta como veio", () => {
    expect(telefone("123")).toBe("123");
  });

  it.each([
    ["ENVIADO", "Enviado", "sucesso"],
    ["SEM_RESULTADO", "Sem resultado", "neutro"],
    ["FALHA_COLETA", "Falha na coleta", "erro"],
    ["COLETANDO", "Coletando", "andamento"],
  ] as const)("status %s", (status, rotulo, tom) => {
    expect(rotuloStatus(status)).toEqual({ rotulo, tom });
  });

  it.each([
    ["PI", "Piauí"],
    ["MA", "Maranhão"],
    ["XX", "XX"],
  ])("UF %s → %s", (sigla, nome) => {
    expect(nomeUf(sigla)).toBe(nome);
  });
});
