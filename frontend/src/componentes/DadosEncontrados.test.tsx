import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DadosEncontrados } from "./DadosEncontrados";
import { execucao } from "../testes/dados";

const dados = execucao().dados_encontrados!;

describe("dados encontrados", () => {
  it("um cartão por praça com os números da consulta", () => {
    render(<DadosEncontrados dados={dados} />);
    const piaui = screen.getByRole("region", { name: "Piauí" });
    expect(within(piaui).getByText("95,7%")).toBeInTheDocument();
    expect(within(piaui).getByText("148.962")).toBeInTheDocument();
    expect(within(piaui).getByText("19.340")).toBeInTheDocument();
    expect(within(piaui).getByText("10.305")).toBeInTheDocument();
  });

  it("informa a data-base de cada bloco", () => {
    render(<DadosEncontrados dados={dados} />);
    expect(screen.getByText(/Junho\/2026/)).toBeInTheDocument();
    expect(screen.getByText(/Julho\/2026/)).toBeInTheDocument();
  });

  it("contexto nacional", () => {
    render(<DadosEncontrados dados={dados} />);
    const nacional = screen.getByRole("region", { name: "Brasil" });
    expect(within(nacional).getByText("77,3%")).toBeInTheDocument();
  });
});
