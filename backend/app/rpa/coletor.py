"""Coleta no site do BCB com Playwright — ver ADR-002 e ADR-008.

Não é desenvolvido em TDD: depende de um site de terceiro. A conversão do
catálogo é pura e testada em `catalogo.py`; este módulo é coberto por testes
marcados como `integration`, fora da suíte padrão.
"""

import re
from pathlib import Path
from types import TracebackType
from typing import Self

from playwright.sync_api import (
    Browser,
    Page,
    Playwright,
    Response,
    sync_playwright,
)
from playwright.sync_api import (
    Error as PlaywrightError,
)

from app.domain.erros import ColetaError, ColetaIndisponivel
from app.rpa.catalogo import Catalogo, Dataset, ItemCatalogo, montar_catalogo

TIMEOUT_PADRAO_MS = 60_000

# Seções localizadas pelo título, não pela posição: sobrevive a reordenação.
TITULOS = {
    Dataset.CONSOLIDADO: "Dados consolidados",
    Dataset.UF: "Dados por unidade da federação",
}


class ColetorBCB:
    """Sessão de navegador na página de consórcios do BCB.

    Uma sessão por vez em cada thread: a API síncrona do Playwright não admite
    duas instâncias abertas na mesma thread. Execuções concorrentes precisam
    de threads distintas — o que o BackgroundTasks do FastAPI já garante.

    Uso:
        with ColetorBCB(url) as coletor:
            catalogo = coletor.ler_catalogo()
            caminho = coletor.baixar(catalogo.mais_recente(Dataset.UF), destino)
    """

    def __init__(
        self, url_pagina: str, headless: bool = True, timeout_ms: int = TIMEOUT_PADRAO_MS
    ) -> None:
        self._url = url_pagina
        self._headless = headless
        self._timeout = timeout_ms
        self._respostas: list[object] = []
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._pagina: Page | None = None
        self._carregada = False

    def __enter__(self) -> Self:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self._headless)
        contexto = self._browser.new_context(accept_downloads=True)
        contexto.set_default_timeout(self._timeout)
        self._pagina = contexto.new_page()
        self._pagina.on("response", self._escutar)
        return self

    def __exit__(
        self,
        tipo: type[BaseException] | None,
        erro: BaseException | None,
        rastro: TracebackType | None,
    ) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def ler_catalogo(self) -> Catalogo:
        """Arquivos disponíveis, montados do JSON que a própria página requisita."""
        self._carregar()
        catalogo = montar_catalogo(self._respostas, self._url)
        if catalogo.vazio:
            # A página carregou sem pedir a lista: costuma ser a API interna fora do ar.
            raise ColetaIndisponivel(
                "catálogo não encontrado: a página não requisitou a lista de arquivos "
                "no formato esperado (ver ADR-008)"
            )
        return catalogo

    def baixar(self, item: ItemCatalogo, destino: Path) -> Path:
        """Escolhe o arquivo no dropdown, clica em baixar e salva em `destino`."""
        self._carregar()
        pagina = self._exigir_pagina()
        titulo = pagina.get_by_role("heading", name=TITULOS[item.dataset], exact=True)

        try:
            titulo.locator("xpath=following::ng-select[1]").click()
            opcao = pagina.locator("ng-dropdown-panel .ng-option").filter(
                has_text=re.compile(rf"^\s*{re.escape(item.rotulo)}\s*\(")
            )
            if opcao.count() == 0:
                raise ColetaError(f"opção '{item.rotulo}' não está no dropdown de {item.dataset}")
            opcao.first.click()

            botao = titulo.locator("xpath=following::button[normalize-space()='Baixar arquivo'][1]")
            with pagina.expect_download() as informacao:
                botao.click()
            download = informacao.value
        except PlaywrightError as erro:
            raise ColetaIndisponivel(f"falha ao baixar {item.nome}: {_resumo(erro)}") from erro

        if download.suggested_filename != item.nome:
            raise ColetaError(
                f"o site entregou '{download.suggested_filename}' em vez de '{item.nome}'"
            )

        destino.mkdir(parents=True, exist_ok=True)
        caminho = destino / item.nome
        download.save_as(caminho)
        return caminho

    def _carregar(self) -> None:
        if self._carregada:
            return
        pagina = self._exigir_pagina()
        try:
            pagina.goto(self._url, wait_until="networkidle")
        except PlaywrightError as erro:
            raise ColetaIndisponivel(
                f"site do BCB indisponível ou lento demais: {_resumo(erro)}"
            ) from erro
        self._rejeitar_cookies(pagina)
        self._carregada = True

    def _rejeitar_cookies(self, pagina: Page) -> None:
        """O banner cobre o conteúdo e intercepta cliques. Ausência não é erro."""
        botao = pagina.get_by_role("button", name="Rejeitar cookies")
        try:
            if botao.is_visible():
                botao.click()
        except PlaywrightError:
            pass

    def _escutar(self, resposta: Response) -> None:
        if resposta.request.resource_type not in ("xhr", "fetch"):
            return
        if "json" not in resposta.headers.get("content-type", ""):
            return
        try:
            self._respostas.append(resposta.json())
        except (PlaywrightError, ValueError):
            pass  # corpo indisponível ou malformado: não é o catálogo

    def _exigir_pagina(self) -> Page:
        if self._pagina is None:
            raise RuntimeError("ColetorBCB deve ser usado dentro de um bloco 'with'")
        return self._pagina


def _resumo(erro: PlaywrightError) -> str:
    return str(erro).splitlines()[0]
