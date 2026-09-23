import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Conexao, SituacaoConexao } from "../api/tipos";
import { rotuloConexao, vigiarConexao } from "./conexao";

const conexao = (situacao: SituacaoConexao): Conexao => ({
  situacao,
  conta: null,
  qr_code: null,
  mensagem: null,
});

describe("vigiar a conexão do WhatsApp", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("consulta depressa enquanto espera o QR code ser lido", async () => {
    const buscar = vi.fn(async () => conexao("AGUARDANDO_QR"));
    vigiarConexao(buscar, () => {}, { rapidoMs: 1000, lentoMs: 10_000 });
    await vi.advanceTimersByTimeAsync(3500);
    expect(buscar).toHaveBeenCalledTimes(4);
  });

  it("conectado, continua vigiando, mas devagar, para notar uma desconexão", async () => {
    const buscar = vi.fn(async () => conexao("CONECTADO"));
    vigiarConexao(buscar, () => {}, { rapidoMs: 1000, lentoMs: 10_000 });
    await vi.advanceTimersByTimeAsync(9000);
    expect(buscar).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1000);
    expect(buscar).toHaveBeenCalledTimes(2);
  });

  it("entrega cada leitura", async () => {
    const fila: SituacaoConexao[] = ["INICIANDO", "AGUARDANDO_QR", "CONECTADO"];
    const buscar = vi.fn(async () => conexao(fila.length > 1 ? fila.shift()! : fila[0]));
    const vistas: SituacaoConexao[] = [];
    vigiarConexao(buscar, (c) => vistas.push(c.situacao), { rapidoMs: 1000, lentoMs: 10_000 });
    await vi.advanceTimersByTimeAsync(2500);
    expect(vistas).toEqual(["INICIANDO", "AGUARDANDO_QR", "CONECTADO"]);
  });

  it("servidor fora do ar vira INDISPONIVEL e a vigília continua", async () => {
    let chamadas = 0;
    const buscar = vi.fn(async () => {
      chamadas += 1;
      if (chamadas === 1) throw new Error("rede");
      return conexao("CONECTADO");
    });
    const vistas: Conexao[] = [];
    vigiarConexao(buscar, (c) => vistas.push(c), { rapidoMs: 1000, lentoMs: 10_000 });
    await vi.advanceTimersByTimeAsync(1500);
    expect(vistas[0].situacao).toBe("INDISPONIVEL");
    expect(vistas[0].mensagem).toMatch(/servidor/);
    expect(vistas[1].situacao).toBe("CONECTADO");
  });

  it("cancelar interrompe a vigília", async () => {
    const buscar = vi.fn(async () => conexao("AGUARDANDO_QR"));
    const cancelar = vigiarConexao(buscar, () => {}, { rapidoMs: 1000, lentoMs: 10_000 });
    await vi.advanceTimersByTimeAsync(500);
    cancelar();
    await vi.advanceTimersByTimeAsync(10_000);
    expect(buscar).toHaveBeenCalledTimes(1);
  });
});

describe("rótulo da conexão", () => {
  it("verde só quando conectado", () => {
    expect(rotuloConexao("CONECTADO")).toEqual({ rotulo: "Conectado", tom: "sucesso" });
    expect(rotuloConexao("AGUARDANDO_QR").tom).toBe("andamento");
    expect(rotuloConexao("DESCONECTADO").tom).toBe("erro");
    expect(rotuloConexao("INDISPONIVEL").tom).toBe("erro");
  });
});
