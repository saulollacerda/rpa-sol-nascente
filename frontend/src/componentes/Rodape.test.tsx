import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Rodape } from "./Rodape";

describe("rodapé", () => {
  it("traz as colunas, as redes sociais e o lema da Sol Nascente", () => {
    render(<Rodape />);
    for (const titulo of ["Motos", "Serviços", "Sol Nascente"]) {
      expect(screen.getByRole("heading", { name: titulo })).toBeInTheDocument();
    }
    expect(screen.getByText("CG 160 Fan")).toBeInTheDocument();
    for (const rede of ["Facebook", "Instagram", "YouTube"]) {
      expect(screen.getByRole("img", { name: rede })).toBeInTheDocument();
    }
    expect(screen.getByText("Desacelere. Seu bem maior é a vida.")).toBeInTheDocument();
    expect(
      screen.getByText(`© ${new Date().getFullYear()} Sol Nascente Motos`),
    ).toBeInTheDocument();
  });

  it("cita o Banco Central como fonte dos dados", () => {
    render(<Rodape />);
    expect(screen.getByText(/Banco Central do Brasil/)).toBeInTheDocument();
  });
});
