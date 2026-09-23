import type { Decisao, Execucao } from "../api/tipos";
import { ehTerminal } from "../dominio/etapas";
import { dataHora, rotuloStatus, telefone } from "../dominio/formatacao";
import { Etapas } from "./Etapas";
import { SeloStatus } from "./SeloStatus";

interface Props {
  execucao: Execucao | null;
  decisao?: Decisao;
}

export function AcompanhamentoExecucao({ execucao, decisao }: Props) {
  if (!execucao) {
    return (
      <div className="vazio">
        <p>Nenhuma consulta em andamento.</p>
        <p>Escolha os parâmetros e clique em <strong>Gerar e enviar relatório</strong>.</p>
      </div>
    );
  }

  const { status } = execucao;
  const falhou = rotuloStatus(status).tom === "erro";

  return (
    <div className="acompanhamento">
      <div className="acompanhamento__topo">
        <h2>Execução #{execucao.id}</h2>
        <SeloStatus status={status} anunciar />
      </div>
      <p className="meta">
        Solicitada em {dataHora(execucao.criado_em)}
        {execucao.tentativas > 1 && ` · ${execucao.tentativas}ª tentativa`}
      </p>

      {execucao.origem_id !== null && (
        <p className="aviso aviso--neutro">
          Dados reaproveitados da execução #{execucao.origem_id} — relatório enviado sem nova
          coleta no Banco Central.
        </p>
      )}

      {decisao === "REUSAR" && !ehTerminal(status) && (
        <p className="aviso aviso--neutro">
          Essa consulta já está em andamento — acompanhe abaixo.
        </p>
      )}

      {decisao === "REUSAR" && status === "SEM_RESULTADO" && (
        <p className="aviso aviso--neutro">
          Essa consulta já foi feita e não teve resultado — não há relatório para enviar.
        </p>
      )}

      <Etapas status={status} />

      {!ehTerminal(status) && status === "COLETANDO" && (
        <p className="meta">Navegando no site do Banco Central — costuma levar uns 10 segundos.</p>
      )}

      {falhou && (
        <div className="aviso aviso--erro" role="alert">
          <strong>{rotuloStatus(status).rotulo}:</strong> {execucao.erro_descricao}
          <p>Clique em Gerar e enviar relatório com os mesmos parâmetros para tentar de novo.</p>
        </div>
      )}

      {status === "SEM_RESULTADO" && (
        <p className="aviso aviso--neutro">
          A administradora não tem dados para esses parâmetros. Nada foi enviado.
        </p>
      )}

      {execucao.mensagem_gerada && (
        <figure className="whatsapp">
          <figcaption>
            {status === "ENVIADO"
              ? `Para ${telefone(execucao.destinatario)} · ${dataHora(execucao.enviado_em ?? execucao.atualizado_em)}`
              : `Não entregue a ${telefone(execucao.destinatario)}`}
          </figcaption>
          <div className="whatsapp__conversa">
            <p className="whatsapp__bolha">{execucao.mensagem_gerada}</p>
          </div>
        </figure>
      )}
    </div>
  );
}
