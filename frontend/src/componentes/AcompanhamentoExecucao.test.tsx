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

  it("reenvio: avisa de qual execução vieram os dados", () => {
    render(<AcompanhamentoExecucao execucao={execucao({ id: 12, origem_id: 7 })} decisao="REENVIAR" />);
    expect(screen.getByText(/dados reaproveitados da execução #7/i)).toBeInTheDocument();
    expect(screen.getByText(/sem nova coleta/i)).toBeInTheDocument();
  });

  it("o aviso de reaproveitamento também aparece ao rever pelo histórico", () => {
    render(<AcompanhamentoExecucao execucao={execucao({ origem_id: 7 })} />);
    expect(screen.getByText(/dados reaproveitados da execução #7/i)).toBeInTheDocument();
  });

  it("clique repetido durante a execução: avisa que já está em andamento", () => {
    render(
      <AcompanhamentoExecucao
        execucao={execucao({ status: "COLETANDO", mensagem_gerada: null })}
        decisao="REUSAR"
      />,
    );
    expect(screen.getByText(/já está em andamento/i)).toBeInTheDocument();
  });

  it("consulta sem resultado repetida: avisa que já foi feita", () => {
    render(
      <AcompanhamentoExecucao
        execucao={execucao({ status: "SEM_RESULTADO", mensagem_gerada: null })}
        decisao="REUSAR"
      />,
    );
    expect(screen.getByText(/já foi feita e não teve resultado/i)).toBeInTheDocument();
  });
});
