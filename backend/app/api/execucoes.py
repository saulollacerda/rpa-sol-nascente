"""Rotas de execução: disparar a consulta, acompanhar e consultar o histórico."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response

from app.api.dependencias import get_servico, get_settings
from app.api.schemas import ExecucaoOut, SolicitacaoIn, SolicitacaoOut
from app.config import Settings
from app.domain.execucao import ParametrosConsulta
from app.domain.servico import ServicoExecucao

router = APIRouter(prefix="/execucoes", tags=["execuções"])

Servico = Annotated[ServicoExecucao, Depends(get_servico)]
Config = Annotated[Settings, Depends(get_settings)]


@router.post("", response_model=SolicitacaoOut, status_code=202)
def solicitar(
    corpo: SolicitacaoIn,
    tarefas: BackgroundTasks,
    resposta: Response,
    servico: Servico,
    settings: Config,
) -> SolicitacaoOut:
    """202 quando a execução é criada ou retentada; 200 quando já existia (ADR-004)."""
    destinatario = corpo.destinatario or settings.whatsapp_destinatario
    if not destinatario:
        # Operator-facing: the missing WHATSAPP_DESTINATARIO is a deploy detail.
        raise HTTPException(422, "Informe o número de WhatsApp que vai receber o relatório.")

    solicitacao = servico.solicitar(
        ParametrosConsulta(
            data_base=corpo.data_base,
            segmento=corpo.segmento,
            ufs=tuple(corpo.ufs),
            cnpj_administradora=corpo.cnpj_administradora,
            top_concorrentes=corpo.top_concorrentes,
            destinatario=destinatario,
        )
    )
    if solicitacao.processar:
        # Função síncrona: o Starlette a roda num pool de threads, o que atende à
        # restrição do Playwright de uma sessão por thread.
        tarefas.add_task(servico.processar, solicitacao.execucao.id)
    else:
        resposta.status_code = 200

    return SolicitacaoOut(
        decisao=solicitacao.decisao.value,
        execucao=ExecucaoOut.de_dominio(solicitacao.execucao),
    )


@router.get("", response_model=list[ExecucaoOut])
def listar(servico: Servico, limite: Annotated[int, Query(ge=1, le=100)] = 20) -> list[ExecucaoOut]:
    return [ExecucaoOut.de_dominio(e) for e in servico.listar(limite)]


@router.get("/{execucao_id}", response_model=ExecucaoOut)
def obter(execucao_id: int, servico: Servico) -> ExecucaoOut:
    execucao = servico.obter(execucao_id)
    if execucao is None:
        raise HTTPException(404, f"execução {execucao_id} não encontrada")
    return ExecucaoOut.de_dominio(execucao)
