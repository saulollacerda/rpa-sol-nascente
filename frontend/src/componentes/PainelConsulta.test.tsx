import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { PainelConsulta } from "./PainelConsulta";
import { OPCOES } from "../testes/dados";

function montar(enviando = false) {
  const onEnviar = vi.fn();
  render(<PainelConsulta opcoes={OPCOES} enviando={enviando} onEnviar={onEnviar} />);
  return { onEnviar, usuario: userEvent.setup() };
}

const botaoEnviar = () => screen.getByRole("button", { name: /gerar e enviar/i });

describe("painel de consulta", () => {
  it("abre com os padrões da Sol Nascente Motos", () => {
    montar();
    expect(screen.getByLabelText("Data-base")).toHaveValue("202607");
    expect(screen.getByRole("option", { name: "Julho/2026" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Piauí" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Maranhão" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "São Paulo" })).toHaveAttribute("aria-pressed", "false");
  });

  it("envia os padrões sem precisar mexer em nada", async () => {
    const { onEnviar, usuario } = montar();
    await usuario.click(botaoEnviar());
    expect(onEnviar).toHaveBeenCalledWith({
      data_base: "202607",
      segmento: 4,
      ufs: ["PI", "MA"],
      cnpj_administradora: "45441789",
      top_concorrentes: 3,
    });
  });

  it("inclui a UF clicada e o destinatário digitado", async () => {
    const { onEnviar, usuario } = montar();
    await usuario.click(screen.getByRole("button", { name: "São Paulo" }));
    await usuario.type(screen.getByLabelText(/WhatsApp/), "+55 86 99999-0000");
    await usuario.click(botaoEnviar());
    expect(onEnviar.mock.calls[0][0]).toMatchObject({
      ufs: ["PI", "MA", "SP"],
      destinatario: "+55 86 99999-0000",
    });
  });

  it("sem UF, avisa e não envia", async () => {
    const { onEnviar, usuario } = montar();
    await usuario.click(screen.getByRole("button", { name: "Piauí" }));
    await usuario.click(screen.getByRole("button", { name: "Maranhão" }));
    await usuario.click(botaoEnviar());
    expect(screen.getByText("Escolha ao menos uma UF")).toBeInTheDocument();
    expect(onEnviar).not.toHaveBeenCalled();
  });

  it("lista só as administradoras do segmento escolhido", async () => {
    const { usuario } = montar();
    const administradora = screen.getByLabelText("Administradora");
    expect(screen.queryByRole("option", { name: "SÓ IMÓVEIS ADM" })).not.toBeInTheDocument();

    await usuario.selectOptions(screen.getByLabelText("Segmento"), "1");
    expect(screen.getByRole("option", { name: "SÓ IMÓVEIS ADM" })).toBeInTheDocument();
    expect(administradora).toHaveValue(""); // a Honda não atua em imóveis
  });

  it("bloqueia o botão enquanto envia", () => {
    montar(true);
    expect(screen.getByRole("button", { name: /gerando/i })).toBeDisabled();
  });
});
