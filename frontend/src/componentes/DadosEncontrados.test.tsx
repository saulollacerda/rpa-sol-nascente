import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DadosEncontrados } from "./DadosEncontrados";
import { execucao } from "../testes/dados";
import type { DadosEncontrados as Dados, Relatorio } from "../api/tipos";

const dados = execucao().dados_encontrados!;
const relatorio = dados.relatorio as Relatorio;

describe("dados encontrados", () => {
  it("o mercado das UFs escolhidas, com os indicadores do trimestre", () => {
    render(<DadosEncontrados dados={dados} />);
    const mercado = screen.getByRole("region", { name: "UFs selecionadas" });
    expect(within(mercado).getByText("750")).toBeInTheDocument();
    expect(within(mercado).getByText("1.000")).toBeInTheDocument(); // contemplações
    expect(within(mercado).getByText("90,0% por lance")).toBeInTheDocument();
    expect(within(mercado).getByText("25,0%")).toBeInTheDocument(); // exclusão
    const pi = within(mercado).getByText("Piauí").closest("li")!;
    expect(within(pi).getByText("95,7% → 96,6%")).toBeInTheDocument();
  });

  it("um cartão por administradora, com o dado nacional marcado", () => {
    render(<DadosEncontrados dados={dados} />);
    const honda = screen.getByRole("region", { name: "ADM CONS NAC HONDA LTDA" });
    expect(within(honda).getByText("93,1%")).toBeInTheDocument();
    expect(within(honda).getByText("🇧🇷 Inadimplência")).toBeInTheDocument();
    expect(within(honda).getByText("10,6%")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "YAMAHA ADM CONS LTDA" })).toBeInTheDocument();
  });

  it("informa a data-base de cada dataset", () => {
    render(<DadosEncontrados dados={dados} />);
    expect(screen.getByText(/Junho\/2026/)).toBeInTheDocument();
    expect(screen.getByText(/Julho\/2026/)).toBeInTheDocument();
  });

  it("sem UF, o mercado é o Brasil", () => {
    const brasil: Dados = { ...dados, relatorio: { ...relatorio, ufs: [], posicoes_uf: [] } };
    render(<DadosEncontrados dados={brasil} />);
    expect(screen.getByRole("region", { name: "Brasil" })).toBeInTheDocument();
  });

  it("execução antiga, de antes do template atual, não quebra a tela", () => {
    const { container } = render(
      <DadosEncontrados dados={{ ...dados, relatorio: { pracas: [], nacional: null } }} />,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
