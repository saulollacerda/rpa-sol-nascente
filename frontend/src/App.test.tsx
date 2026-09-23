import { render, screen, within } from "@testing-library/react";
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
  obterConexao: vi.fn(),
  reconectarWhatsApp: vi.fn(),
}));

describe("app", () => {
  beforeEach(() => {
    vi.mocked(cliente.obterOpcoes).mockResolvedValue(OPCOES);
    vi.mocked(cliente.listarExecucoes).mockResolvedValue([]);
    vi.mocked(cliente.solicitar).mockResolvedValue({ execucao: execucao(), decisao: "CRIAR" });
    vi.mocked(cliente.obterConexao).mockResolvedValue({
      situacao: "AGUARDANDO_QR",
      conta: null,
      qr_code: "data:image/png;base64,AAA",
      mensagem: null,
    });
  });

  it("o WhatsApp aparece ao lado da nova consulta, com o QR code para conectar", async () => {
    render(<App />);
    const cartao = await screen.findByRole("region", { name: "WhatsApp" });
    expect(await within(cartao).findByRole("img", { name: /qr code/i })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Nova consulta" })).toBeInTheDocument();
  });

  it("abre só com a nova consulta; o acompanhamento aparece ao gerar o relatório", async () => {
    render(<App />);
    const botao = await screen.findByRole("button", { name: /gerar e enviar/i });
    expect(screen.queryByRole("region", { name: "Acompanhamento" })).not.toBeInTheDocument();

    await userEvent.click(botao);
    expect(await screen.findByRole("region", { name: "Acompanhamento" })).toBeInTheDocument();
  });
});
