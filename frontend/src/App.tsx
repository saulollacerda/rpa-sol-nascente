import { useCallback, useEffect, useState } from "react";
import { ErroApi, listarExecucoes, obterExecucao, solicitar } from "./api/cliente";
import type { Decisao, Execucao, Solicitacao } from "./api/tipos";
import { AcompanhamentoExecucao } from "./componentes/AcompanhamentoExecucao";
import { DadosEncontrados } from "./componentes/DadosEncontrados";
import { Historico } from "./componentes/Historico";
import { PainelConsulta } from "./componentes/PainelConsulta";
import { acompanhar } from "./dominio/acompanhar";
import { ehTerminal } from "./dominio/etapas";
import { useOpcoes } from "./hooks/useOpcoes";

export function App() {
  const { opcoes, erro: erroOpcoes, carregando, recarregar } = useOpcoes();
  const [atual, setAtual] = useState<Execucao | null>(null);
  const [decisao, setDecisao] = useState<Decisao>();
  const [enviando, setEnviando] = useState(false);
  const [erroEnvio, setErroEnvio] = useState<string | null>(null);
  const [historico, setHistorico] = useState<Execucao[]>([]);

  const atualizarHistorico = useCallback(() => {
    listarExecucoes().then(setHistorico).catch(() => {});
  }, []);

  useEffect(atualizarHistorico, [atualizarHistorico]);

  // Acompanha só enquanto a execução não terminou; o id muda a cada nova consulta.
  const emAndamento = atual && !ehTerminal(atual.status) ? atual.id : null;
  useEffect(() => {
    if (emAndamento === null) return;
    return acompanhar(emAndamento, obterExecucao, (e) => {
      setAtual(e);
      if (ehTerminal(e.status)) atualizarHistorico();
    });
  }, [emAndamento, atualizarHistorico]);

  const enviar = async (solicitacao: Solicitacao) => {
    setEnviando(true);
    setErroEnvio(null);
    try {
      const resposta = await solicitar(solicitacao);
      setAtual(resposta.execucao);
      setDecisao(resposta.decisao);
      atualizarHistorico();
    } catch (e) {
      setErroEnvio(e instanceof ErroApi ? e.message : "falha inesperada ao enviar");
    } finally {
      setEnviando(false);
    }
  };

  const selecionar = (id: number) => {
    const escolhida = historico.find((e) => e.id === id);
    if (escolhida) {
      setAtual(escolhida);
      setDecisao(undefined);
    }
  };

  return (
    <div className="pagina">
      <header className="cabecalho">
        <div className="marca" aria-hidden="true" />
        <div>
          <h1>Radar de Consórcio</h1>
          <p>Sol Nascente Motos · dados públicos do Banco Central</p>
        </div>
      </header>

      <main className="grade">
        <section className="cartao" aria-labelledby="titulo-consulta">
          <h2 id="titulo-consulta">Nova consulta</h2>
          {carregando && (
            <div className="carregando" role="status">
              <span className="giro" aria-hidden="true" />
              Consultando o catálogo do Banco Central… a primeira carga leva cerca de 10 segundos.
            </div>
          )}
          {erroOpcoes && (
            <div className="aviso aviso--erro" role="alert">
              {erroOpcoes}
              <button type="button" className="botao-secundario" onClick={recarregar}>
                Tentar de novo
              </button>
            </div>
          )}
          {opcoes && <PainelConsulta opcoes={opcoes} enviando={enviando} onEnviar={enviar} />}
          {erroEnvio && (
            <p className="aviso aviso--erro" role="alert">
              {erroEnvio}
            </p>
          )}
        </section>

        <section className="cartao" aria-label="Acompanhamento">
          <AcompanhamentoExecucao execucao={atual} decisao={decisao} />
          {atual?.dados_encontrados && <DadosEncontrados dados={atual.dados_encontrados} />}
        </section>
      </main>

      <section className="cartao historico-cartao" aria-labelledby="titulo-historico">
        <h2 id="titulo-historico">Histórico</h2>
        <Historico execucoes={historico} selecionada={atual?.id} onSelecionar={selecionar} />
      </section>

      <footer className="rodape">
        Fonte: Banco Central do Brasil — Bancos de dados de consórcios. Segmento 4 = motocicletas e
        motonetas.
      </footer>
    </div>
  );
}
