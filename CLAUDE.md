# CLAUDE.md

## O projeto

RPA que coleta dados públicos do Banco Central sobre o mercado de consórcio de **motocicletas** (segmento 4) e envia um relatório de inteligência comercial por WhatsApp. Cliente: Sol Nascente Motos, concessionária Honda com praças em **PI e MA**.

Fluxo: painel de parâmetros → Playwright navega o site do BCB → baixa ZIPs → parseia CSVs → apura métricas → gera mensagem → envia WhatsApp → registra execução.

- Produto e requisitos: [`docs/PRD.md`](docs/PRD.md)
- Decisões de arquitetura: [`docs/adr/`](docs/adr/README.md)
- Registro de decisões técnicas: [`docs/DECISOES-TECNICAS.md`](docs/DECISOES-TECNICAS.md)

## Estrutura

```
backend/
  app/
    api/        rotas FastAPI, schemas de entrada e saída
    domain/     entidades, regras de negócio, montagem do relatório
    rpa/        Playwright: navegação e download
    parsing/    unzip, leitura de CSV, normalização
    infra/      SQLAlchemy, adapters de WhatsApp, logging
    config.py   pydantic-settings
  tests/
    fixtures/   ZIPs e CSVs de amostra (versionados)
frontend/
  src/          React + TypeScript (Vite)
docs/
  PRD.md
  adr/
backend/data/   artefatos baixados do BCB e banco SQLite (ignorado pelo git)
docker-compose.yml
backend/Dockerfile
```

## Regras de arquitetura

**Direção da dependência: `api → domain → infra`.**

`domain/` é puro. Não importa Playwright, SQLAlchemy, `httpx` nem nada que toque I/O. Cálculo de share, consolidação por UF e composição da mensagem precisam ser testáveis sem rede e sem banco. Se uma função de domínio precisa de dados externos, eles chegam como argumento.

Integrações externas entram por `Protocol` definido no domínio e implementado em `infra/` — é assim que `WhatsAppSender` tem adapter real e fake ([ADR-003](docs/adr/ADR-003-integracao-whatsapp.md)).

## Padrões

- **Idioma:** código, nomes de variáveis e comentários em inglês; domínio, UI e mensagens ao usuário em português. Nomes de colunas do BCB ficam como vêm na fonte.
- **Formatação:** `ruff` + `black`. Type hints obrigatórios em tudo que é público.
- **Erros:** exceções de domínio próprias (`ColetaError`, `ParsingError`, `EnvioError`). Não deixar exceção de biblioteca vazar para a camada de API — capturar, traduzir e registrar.
- **Logs:** logging estruturado, com `execucao_id` em toda linha emitida durante uma execução. Chaves sensíveis são mascaradas antes da serialização.
- **Testes: o projeto é desenvolvido em TDD.** Escreva o teste que falha antes do código que o faz passar. Ferramenta: `pytest`.

## Estratégia de teste

| Camada | Teste primeiro? | Como |
|---|---|---|
| `domain/` | ✅ sempre | funções puras, sem rede nem banco |
| `parsing/` | ✅ sempre | fixture ZIP em `backend/tests/fixtures/` |
| `api/` | ✅ sempre | `TestClient` do FastAPI |
| `infra/whatsapp` | ✅ sempre | via `FakeSender` |
| `infra/db` | ⚠️ parcial | SQLite em memória |
| `rpa/` | ❌ não | spike descartável + teste `@pytest.mark.integration`, fora da suíte padrão |

TDD contra um site de terceiro não é TDD. Para o `rpa/`, o que se testa é o contrato — dado um ZIP, o que a camada devolve — e isso já é coberto por `parsing/`.

**Fixtures ficam em `backend/tests/fixtures/` e são versionadas.** Não confundir com `data/`, que é ignorado pelo git — colocar fixture lá quebra a suíte em qualquer máquina nova.

Os números de referência abaixo são o oráculo do parser: sirva-se deles nas assertivas.

## Armadilhas da fonte BCB

Já verificadas nos arquivos reais — não redescobrir a cada sessão:

- A URL pública `bcb.gov.br/estabilidadefinanceira/consorciobd` é **SPA Angular**: o HTML tem 2.871 bytes e zero dados. `curl` nela não serve para nada.
- **Existe uma página ASP legada que responde a `curl` — e ela está defasada em ~2 meses.** `fis/consorcios/port/consorcio_banco_de_dados.asp` usa `<select>` nativo e lista até Maio/2026 (consolidado) e Março/2026 (UF), enquanto a página real já tem Julho/2026 e Junho/2026. **Não automatizar contra o ASP** — entrega dado velho sem erro. Ver [ADR-002](docs/adr/ADR-002-fonte-bcb-e-estrategia-de-rpa.md).
- O dropdown da página atual é **`ng-select`** (`<div class="ng-option">`), não `<select>`. Não há formulário para submeter: sem browser real não há interação possível.
- Caminho real dos arquivos:
  ```
  /content/estabilidadefinanceira/consorcio-banco-de-dados/
      dados-consolidados/AAAAMMConsorcios.zip
      dados-por-unidade-da-federacao/AAAAMMConsorcios_UF.zip
      dados-contabeis-descontinuados/      → ConsorciosAdministradoras_*.zip, descontinuado, não usar
  ```
- **A página pede a lista de arquivos a uma API JSON** (`Documentos/byListGuid`, resposta `{"conteudo": [...]}`, com `Url`, `Nome`, `Tamanho`, `DataPublicacao`, `DataDocumento`). O robô **escuta** essa resposta; **não chamar o endpoint direto** nem fixar o `guid` no código. Classificar o dataset pelo `Nome` do arquivo. Ver [ADR-008](docs/adr/ADR-008-catalogo-pela-rede-da-pagina.md).
- **Banner de cookies** cobre o conteúdo: clicar em "Rejeitar cookies" antes de interagir.
- Seções localizadas pelo título `<h4>` exato ("Dados consolidados", "Dados por unidade da federação"), não pela posição. O botão "Baixar arquivo" fica **desabilitado até escolher uma opção**.
- Rótulo da opção: `202606Consorcios_UF (103.4 Kb)`. Sem virtual scroll: todas as opções vêm na lista.
- CSVs em **`windows-1252`**, separador **`;`**, decimal com **vírgula** (`23,2`).
- `Nome_da_Administradora` vem com **padding de espaços** — sem `strip()` o agrupamento duplica registros.
- `CNPJ_da_Administradora` é só a **raiz de 8 dígitos zero-padded** (`00000776`). Manter como string.
- O cabeçalho começa com `#` (`#Nome_da_Administradora`).
- O dicionário declara `Data_base` como `AAAA-MM`, mas o arquivo traz `202606`. Confiar no arquivo.
- Consolidado é **mensal**, UF é **trimestral**. As data-bases não coincidem.
- `Código_do_segmento` **4 = motocicletas e motonetas**. É o segmento do produto.

## Números de referência

Para validar que o parsing está correto (consolidado **Julho/2026**, UF **Junho/2026**, segmento 4):

- Nacional: 3.319.425 cotas ativas, 125 administradoras. Honda 2.565.256 (**77,3%**), taxa 23,2%, 3.760 grupos.
- PI: 155.648 ativos, 40 administradoras. Honda 148.962 (**95,7%**), 19.340 adesões, 10.305 contemplados no trimestre.
- MA: 249.533 ativos, 45 administradoras. Honda 228.238 (**91,5%**), 27.261 adesões, 13.402 contemplados no trimestre.

Contagem de linhas: `Segmentos_Consolidados.csv` 750 · `Consorcios_UF.csv` 7.667.

## Git

**Nunca commitar direto na `main`.** A `main` só recebe merge da `develop`, e representa o que está estável.

```
main                      estável; só recebe merge de develop
└── develop               branch de integração; base de todo trabalho
    ├── feat/…            funcionalidade nova
    ├── fix/…             correção de bug
    ├── refactor/…        mudança interna, sem alterar comportamento
    ├── test/…            só testes
    ├── docs/…            só documentação
    └── chore/…           build, dependências, configuração
```

Toda branch sai da `develop` e volta pra `develop`. Nome em kebab-case, descrevendo o objetivo e não o arquivo:

```
feat/coleta-playwright-bcb
fix/encoding-cp1252-nome-administradora
test/parser-segmentos-consolidados
```

### Commits

Padrão [Conventional Commits](https://www.conventionalcommits.org/): `tipo: descrição no imperativo`.

```
feat: adiciona coleta dos ZIPs via Playwright
fix: preserva zeros à esquerda no CNPJ da administradora
test: cobre parser de Segmentos_Consolidados
docs: registra decisão de TDD
chore: configura ruff e black
```

Os tipos são os mesmos dos prefixos de branch. Descrição em português, minúscula, sem ponto final.

### Fluxo

```bash
git switch develop && git pull
git switch -c feat/coleta-playwright-bcb
# … trabalho, em ciclos de TDD …
git switch develop && git merge --no-ff feat/coleta-playwright-bcb
```

`--no-ff` preserva o agrupamento dos commits da feature no histórico.

Em TDD, o commit natural é o ciclo fechado: teste + implementação que o faz passar, juntos. Commitar um teste vermelho deixa a `develop` com a suíte quebrada.

## Comandos

### Com Docker (recomendado)

Da raiz do projeto. Não exige Python, uv nem Playwright instalados — ver [ADR-007](docs/adr/ADR-007-empacotamento-com-docker.md).

```bash
docker compose up                              # sobe em http://localhost:8000
docker compose run --rm backend pytest         # suíte
docker compose run --rm backend ruff check .   # lint
docker compose build                           # rebuild após mudar dependências
```

O Chromium já vem na imagem: **não rode `playwright install` dentro do container.**

Dentro do container não há servidor gráfico, então `PLAYWRIGHT_HEADLESS` é sempre `true`. Para ver a automação navegando numa janela, rode no host.

### Direto no host

Gerenciador de pacotes: **`uv`**. Todos os comandos rodam a partir de `backend/`.

```bash
uv sync                      # cria .venv e instala dependências
uv run pytest                # suíte padrão (exclui os testes de integração)
uv run pytest -m integration # só os que batem no site do BCB
uv run ruff check .          # lint
uv run black .               # formatação
uv run uvicorn app.main:app --reload
```

`uv run <cmd>` dispensa ativar o venv manualmente.

Ainda não instalado, necessário antes de mexer em `rpa/` **fora do Docker**:

```bash
uv run playwright install chromium   # ~150 MB
```

## Nunca commitar

`.env` · `docs/*.pdf` (enunciado do desafio) · `data/` · `*.db`
