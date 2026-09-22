import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { acompanhar } from "./acompanhar";
import { execucao } from "../testes/dados";
import type { Status } from "../api/tipos";

describe("acompanhar uma execução", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  function sequencia(...status: Status[]) {
    const fila = [...status];
    return vi.fn(async () => execucao({ status: fila.length > 1 ? fila.shift()! : fila[0] }));
  }

  it("consulta até chegar a um status final e para", async () => {
    const buscar = sequencia("COLETANDO", "PROCESSANDO", "ENVIADO");
    const vistos: Status[] = [];
    acompanhar(1, buscar, (e) => vistos.push(e.status), 1000);

    await vi.advanceTimersByTimeAsync(10_000);
    expect(vistos).toEqual(["COLETANDO", "PROCESSANDO", "ENVIADO"]);
    expect(buscar).toHaveBeenCalledTimes(3);
  });

  it("cancelar interrompe a consulta", async () => {
    const buscar = sequencia("COLETANDO");
    const cancelar = acompanhar(1, buscar, () => {}, 1000);
    await vi.advanceTimersByTimeAsync(1500);
    cancelar();
    const antes = buscar.mock.calls.length;
    await vi.advanceTimersByTimeAsync(10_000);
    expect(buscar.mock.calls.length).toBe(antes);
  });

  it("erro de rede não derruba o acompanhamento", async () => {
    let chamadas = 0;
    const buscar = vi.fn(async () => {
      chamadas += 1;
      if (chamadas === 1) throw new Error("rede");
      return execucao({ status: "ENVIADO" });
    });
    const vistos: Status[] = [];
    acompanhar(1, buscar, (e) => vistos.push(e.status), 1000);
    await vi.advanceTimersByTimeAsync(5000);
    expect(vistos).toEqual(["ENVIADO"]);
  });
});
