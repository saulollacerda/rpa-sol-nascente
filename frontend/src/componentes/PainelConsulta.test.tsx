import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { PainelConsulta } from "./PainelConsulta";
import { OPCOES } from "../testes/dados";

function montar(enviando = false, opcoes = OPCOES) {
  const onEnviar = vi.fn();
  render(<PainelConsulta opcoes={opcoes} enviando={enviando} onEnviar={onEnviar} />);
  return { onEnviar, usuario: userEvent.setup() };
}

const botaoEnviar = () => screen.getByRole("button", { name: /gerar e enviar/i });

describe("painel de consulta", () => {
  it("abre com os padrões da Sol Nascente Motos", () => {
    montar();
    expect(screen.getByLabelText("Data-base")).toHaveValue("202607");
    expect(screen.getByRole("option", { name: "Julho/2026" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Piauí" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Maranhão" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: "São Paulo" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
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

  it("avisa do telefone inválido ao sair do campo e some ao corrigir", async () => {
    const { onEnviar, usuario } = montar();
    const campo = screen.getByLabelText(/WhatsApp/);
    expect(campo).toHaveAttribute("placeholder", "Insira seu número de telefone");
    await usuario.type(campo, "86 9889-6964");
    await usuario.tab();
    expect(screen.getByText(/incompleto/)).toBeInTheDocument();
    expect(campo).toHaveAttribute("aria-invalid", "true");

    await usuario.click(botaoEnviar());
    expect(onEnviar).not.toHaveBeenCalled();

    await usuario.clear(campo);
    await usuario.type(campo, "86999990000");
    expect(screen.queryByText(/incompleto/)).not.toBeInTheDocument();
    expect(campo).toHaveAttribute("aria-invalid", "false");
  });

  it("sem número padrão no servidor, pede o WhatsApp antes de enviar", async () => {
    const semPadrao = { ...OPCOES, padrao: { ...OPCOES.padrao, tem_destinatario_padrao: false } };
    const { onEnviar, usuario } = montar(false, semPadrao);
    await usuario.click(botaoEnviar());
    expect(
      screen.getByText("Informe o número de WhatsApp que vai receber o relatório."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/WhatsApp/)).toHaveAttribute("aria-invalid", "true");
    expect(onEnviar).not.toHaveBeenCalled();
  });

  it("sem praça, avisa e não envia", async () => {
    const { onEnviar, usuario } = montar();
    await usuario.click(screen.getByRole("button", { name: "Piauí" }));
    await usuario.click(screen.getByRole("button", { name: "Maranhão" }));
    await usuario.click(botaoEnviar());
    expect(screen.getByText("Escolha ao menos uma praça")).toBeInTheDocument();
    expect(onEnviar).not.toHaveBeenCalled();
  });

  it("sem data-base, segmento e administradora, avisa em cada campo", async () => {
    const { onEnviar, usuario } = montar();
    await usuario.selectOptions(screen.getByLabelText("Data-base"), "");
    await usuario.selectOptions(screen.getByLabelText("Segmento"), "");
    await usuario.click(botaoEnviar());

    expect(screen.getByText("Escolha a data-base", { selector: "p" })).toBeInTheDocument();
    expect(screen.getByText("Escolha o segmento", { selector: "p" })).toBeInTheDocument();
    expect(screen.getByText("Escolha a administradora", { selector: "p" })).toBeInTheDocument();
    for (const campo of ["Data-base", "Segmento", "Administradora"]) {
      expect(screen.getByLabelText(campo)).toHaveAttribute("aria-invalid", "true");
    }
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
