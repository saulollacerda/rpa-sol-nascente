import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Historico } from "./Historico";
import { execucao } from "../testes/dados";

describe("histórico", () => {
  it("vazio", () => {
    render(<Historico execucoes={[]} onSelecionar={vi.fn()} />);
    expect(screen.getByText(/nenhuma execução/i)).toBeInTheDocument();
  });

  it("uma linha por execução com o que o enunciado pede", () => {
    render(
      <Historico
        execucoes={[execucao(), execucao({ id: 2, status: "FALHA_ENVIO" })]}
        onSelecionar={vi.fn()}
      />,
    );
    expect(screen.getAllByRole("row")).toHaveLength(3); // cabeçalho + 2
    expect(screen.getAllByText("Julho/2026")).toHaveLength(2);
    expect(screen.getByText("Falha no envio")).toBeInTheDocument();
    expect(screen.getAllByText("MA, PI")).toHaveLength(2);
  });

  it("clicar abre a execução", async () => {
    const onSelecionar = vi.fn();
    render(<Historico execucoes={[execucao({ id: 9 })]} onSelecionar={onSelecionar} />);
    await userEvent.click(screen.getByRole("button", { name: /ver execução 9/i }));
    expect(onSelecionar).toHaveBeenCalledWith(9);
  });
});
