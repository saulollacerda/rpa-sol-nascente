import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Conexao } from "../api/tipos";
import { ConexaoWhatsApp } from "./ConexaoWhatsApp";

const QR = "data:image/png;base64,iVBORw0KGgo";

function conexao(parcial: Partial<Conexao>): Conexao {
  return { situacao: "CONECTADO", conta: null, qr_code: null, mensagem: null, ...parcial };
}

function renderizar(c: Conexao | null, onReconectar = vi.fn()) {
  render(<ConexaoWhatsApp conexao={c} reconectando={false} onReconectar={onReconectar} />);
  return onReconectar;
}

describe("conexão do WhatsApp", () => {
  it("antes da primeira leitura, avisa que está verificando", () => {
    renderizar(null);
    expect(screen.getByRole("status")).toHaveTextContent(/verificando/i);
  });

  it("aguardando: mostra o QR code e como escanear", () => {
    renderizar(conexao({ situacao: "AGUARDANDO_QR", qr_code: QR }));
    expect(screen.getByRole("status")).toHaveTextContent("Aguardando leitura");
    expect(screen.getByRole("img", { name: /qr code/i })).toHaveAttribute("src", QR);
    expect(screen.getByText(/dispositivos conectados/i)).toBeInTheDocument();
  });

  it("conectado: o QR code sai e fica só o status, com a conta", () => {
    renderizar(conexao({ situacao: "CONECTADO", conta: "Sol Nascente Demo (558699990000)" }));
    expect(screen.getByRole("status")).toHaveTextContent("Conectado");
    expect(screen.queryByRole("img", { name: /qr code/i })).not.toBeInTheDocument();
    expect(screen.getByText(/Sol Nascente Demo/)).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("desconectado: oferece gerar um QR code novo", async () => {
    const onReconectar = renderizar(conexao({ situacao: "DESCONECTADO" }));
    expect(screen.getByRole("status")).toHaveTextContent("Desconectado");
    await userEvent.click(screen.getByRole("button", { name: /gerar qr code/i }));
    expect(onReconectar).toHaveBeenCalledOnce();
  });

  it("gerando: o botão fica desabilitado", () => {
    render(
      <ConexaoWhatsApp
        conexao={conexao({ situacao: "DESCONECTADO" })}
        reconectando
        onReconectar={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: /gerando/i })).toBeDisabled();
  });

  it("iniciando: sem QR code nem botão", () => {
    renderizar(conexao({ situacao: "INICIANDO" }));
    expect(screen.getByRole("status")).toHaveTextContent("Iniciando");
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("indisponível: explica o motivo", () => {
    renderizar(conexao({ situacao: "INDISPONIVEL", mensagem: "WAHA não está acessível" }));
    expect(screen.getByRole("alert")).toHaveTextContent("WAHA não está acessível");
  });
});
