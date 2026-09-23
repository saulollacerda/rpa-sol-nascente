import { useCallback, useEffect, useState } from "react";
import { ErroApi, listarExecucoes, obterExecucao, solicitar } from "./api/cliente";
import type { Decisao, Execucao, Solicitacao } from "./api/tipos";
import { AcompanhamentoExecucao } from "./componentes/AcompanhamentoExecucao";
import { ConexaoWhatsApp } from "./componentes/ConexaoWhatsApp";
import { DadosEncontrados } from "./componentes/DadosEncontrados";
import { Historico } from "./componentes/Historico";
import { Logo } from "./componentes/Logo";
import { PainelConsulta } from "./componentes/PainelConsulta";
import { Rodape } from "./componentes/Rodape";
import { acompanhar } from "./dominio/acompanhar";
import { ehTerminal } from "./dominio/etapas";
import { useConexao } from "./hooks/useConexao";
import { useOpcoes } from "./hooks/useOpcoes";

export function App() {
  const { opcoes, erro: erroOpcoes, carregando, recarregar } = useOpcoes();
  const { conexao, reconectando, reconectar } = useConexao();
  const [atual, setAtual] = useState<Execucao | null>(null);
  const [decisao, setDecisao] = useState<Decisao>();
  const [enviando, setEnviando] = useState(false);
  const [erroEnvio, setErroEnvio] = useState<string | null>(null);
  const [historico, setHistorico] = useState<Execucao[]>([]);

  const atualizarHistorico = useCallback(() => {
    listarExecucoes()
      .then(setHistorico)
      .catch(() => {});
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
    <>
      <header className="topo">
        <div className="topo__conteudo">
          <Logo />
        </div>
      </header>

      <div className="pagina">
        <div className="titulo-pagina">
          <h1>Radar de Consórcio</h1>
          <p>Mercado de consórcio de motos no Piauí e no Maranhão, com dados do Banco Central.</p>
        </div>

        <main className={atual ? "grade" : "grade grade--sozinha"}>
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

          <div className="coluna">
            <section className="cartao" aria-labelledby="titulo-whatsapp">
              <ConexaoWhatsApp
                conexao={conexao}
                reconectando={reconectando}
                onReconectar={reconectar}
              />
            </section>

            {atual && (
              <section className="cartao cartao--entrando" aria-label="Acompanhamento">
                <AcompanhamentoExecucao execucao={atual} decisao={decisao} />
                {atual.dados_encontrados && <DadosEncontrados dados={atual.dados_encontrados} />}
              </section>
            )}
          </div>
        </main>

        <section className="cartao historico-cartao" aria-labelledby="titulo-historico">
          <h2 id="titulo-historico">Histórico</h2>
          <Historico execucoes={historico} selecionada={atual?.id} onSelecionar={selecionar} />
        </section>
      </div>

      <Rodape />
    </>
  );
}
