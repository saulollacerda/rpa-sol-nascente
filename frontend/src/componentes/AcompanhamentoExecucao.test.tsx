import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AcompanhamentoExecucao } from "./AcompanhamentoExecucao";
import { execucao } from "../testes/dados";

describe("acompanhamento da execução", () => {
  it("sem execução, convida a começar", () => {
    render(<AcompanhamentoExecucao execucao={null} />);
    expect(screen.getByText(/nenhuma consulta/i)).toBeInTheDocument();
  });

  it("mostra as etapas com o estado de cada uma", () => {
    render(<AcompanhamentoExecucao execucao={execucao({ status: "COLETANDO", mensagem_gerada: null })} />);
    const etapas = within(screen.getByRole("list", { name: "Etapas" })).getAllByRole("listitem");
    expect(etapas.map((e) => e.dataset.estado)).toEqual([
      "feito", "atual", "pendente", "pendente", "pendente", "pendente",
    ]);
  });

  it("enviado: a mensagem aparece como no WhatsApp, com o destinatário", () => {
    render(<AcompanhamentoExecucao execucao={execucao()} />);
    expect(screen.getByText(/📊 RADAR DE CONSÓRCIO/)).toBeInTheDocument();
    expect(screen.getByText(/\+55 86 99999-0000/)).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Enviado");
  });

  it("falha: mostra o motivo e como tentar de novo", () => {
    render(
      <AcompanhamentoExecucao
        execucao={execucao({
          status: "FALHA_COLETA",
          erro_tipo: "ColetaError",
          erro_descricao: "site do BCB indisponível",
          mensagem_gerada: null,
        })}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("site do BCB indisponível");
    expect(screen.getByRole("alert")).toHaveTextContent(/tentar de novo/i);
  });

  it("sem resultado: explica que nada foi enviado, sem tom de erro", () => {
    render(
      <AcompanhamentoExecucao
        execucao={execucao({ status: "SEM_RESULTADO", mensagem_gerada: null })}
      />,
    );
    expect(screen.getByText(/nada foi enviado/i)).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("pedido repetido: avisa que nada foi reenviado", () => {
    render(<AcompanhamentoExecucao execucao={execucao()} decisao="REUSAR" />);
    expect(screen.getByText(/nada foi reenviado/i)).toBeInTheDocument();
  });
});
