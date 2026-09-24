"""Exceções de domínio.

Ficam aqui, e não nas camadas que as lançam, para que o serviço de execução
possa tratá-las sem importar rpa/ ou parsing/ — ver a regra de dependência
do ADR-001, verificada em tests/test_arquitetura.py.
"""


class ErroDeDominio(Exception):
    """Base das falhas esperadas do fluxo."""


class ColetaError(ErroDeDominio):
    """Falha ao obter os dados na fonte: site fora do ar, layout mudou, arquivo ausente."""


class ColetaIndisponivel(ColetaError):
    """Falha transitória: site fora do ar, lento ou download interrompido. Vale tentar de novo.

    O resto da ColetaError é definitivo (data-base não publicada, layout mudou):
    tentar de novo só atrasaria o mesmo erro.
    """


class ParsingError(ErroDeDominio):
    """Falha ao ler ou interpretar um arquivo da fonte."""


class EnvioError(ErroDeDominio):
    """Falha ao entregar a mensagem pelo WhatsApp."""


class TransicaoInvalida(ErroDeDominio):
    """Mudança de status que a máquina de estados do ADR-004 não permite."""


class ExecucaoInterrompida(ErroDeDominio):
    """O processo parou com a execução em andamento: queda, restart ou deploy."""


class ExecucaoDuplicada(ErroDeDominio):
    """Já existe execução com a mesma chave de idempotência."""

    def __init__(self, execucao_id: int) -> None:
        super().__init__(f"já existe a execução {execucao_id} com os mesmos parâmetros")
        self.execucao_id = execucao_id
