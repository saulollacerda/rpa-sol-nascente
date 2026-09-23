import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import * as cliente from "./api/cliente";
import { execucao, OPCOES } from "./testes/dados";

vi.mock("./api/cliente", async (original) => ({
  ...(await original<typeof cliente>()),
  obterOpcoes: vi.fn(),
  listarExecucoes: vi.fn(),
  solicitar: vi.fn(),
  obterExecucao: vi.fn(),
}));

describe("app", () => {
  beforeEach(() => {
    vi.mocked(cliente.obterOpcoes).mockResolvedValue(OPCOES);
    vi.mocked(cliente.listarExecucoes).mockResolvedValue([]);
    vi.mocked(cliente.solicitar).mockResolvedValue({ execucao: execucao(), decisao: "CRIAR" });
  });

  it("abre só com a nova consulta; o acompanhamento aparece ao gerar o relatório", async () => {
    render(<App />);
    const botao = await screen.findByRole("button", { name: /gerar e enviar/i });
    expect(screen.queryByRole("region", { name: "Acompanhamento" })).not.toBeInTheDocument();

    await userEvent.click(botao);
    expect(await screen.findByRole("region", { name: "Acompanhamento" })).toBeInTheDocument();
  });
});
