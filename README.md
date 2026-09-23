# Radar de Consórcio de Motos

RPA que consulta os dados públicos de consórcio do **Banco Central do Brasil**, monta um relatório de inteligência comercial sobre o mercado de **motocicletas** e envia esse relatório por **WhatsApp**. Cada execução fica registrada.

O cliente é a **Sol Nascente Motos**, concessionária Honda com lojas no Piauí e no Maranhão. O relatório responde às perguntas do gestor comercial: quantas pessoas aderiram a consórcio de moto nas praças dele no trimestre, quantas foram contempladas (e têm carta de crédito para comprar uma moto) e se a Honda está ganhando ou perdendo espaço para a concorrência.

```
Painel → Playwright navega no site do BCB → baixa os ZIPs → lê os CSVs → calcula as métricas
       → gera a mensagem → envia pelo WhatsApp → registra a execução
```

<p>
  <img alt="Python 3.12+" src="https://img.shields.io/badge/python-3.12%2B-3776AB">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688">
  <img alt="Playwright" src="https://img.shields.io/badge/Playwright-2EAD33">
  <img alt="React + TypeScript" src="https://img.shields.io/badge/React%20%2B%20TypeScript-61DAFB">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-003B57">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-2496ED">
</p>

## Sumário

- [Início rápido](#início-rápido)
- [Instalação e execução passo a passo](#instalação-e-execução-passo-a-passo)
- [Configuração](#configuração)
- [Usando o painel](#usando-o-painel)
- [API](#api)
- [Testes](#testes)
- [Execução sem Docker](#execução-sem-docker)
- [Arquitetura](#arquitetura)
- [Como o desafio foi atendido](#como-o-desafio-foi-atendido)
- [Solução de problemas](#solução-de-problemas)
- [Limitações e caminho para produção](#limitações-e-caminho-para-produção)
- [Documentação](#documentação)

---

## Início rápido

Pré-requisitos: **Docker** com Docker Compose v2, e um **celular com WhatsApp** para conectar o número que envia. Use um chip dedicado ([por quê](#whatsapp-por-que-um-chip-dedicado)).

```bash
git clone <url-do-repositório> rpa-sol-nascente && cd rpa-sol-nascente

cp backend/.env.example backend/.env
# edite backend/.env: preencha WAHA_API_KEY (ex.: openssl rand -hex 32)

# Só em Mac com Apple Silicon (M1/M2/M3…):
echo "WAHA_TAG=arm" > .env

docker compose up
```

Abra **http://localhost:5173**, escaneie o QR code que aparece no cartão **WhatsApp** e clique em **Gerar e enviar relatório**.

---

## Instalação e execução passo a passo

### 1. Pré-requisitos

| Ferramenta | Para quê |
|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) (ou Docker Engine + Compose v2) | sobe backend, frontend e WhatsApp com um comando |
| Um celular com WhatsApp | conectar o número que vai **enviar** os relatórios |
| Acesso à internet | o robô navega no site do Banco Central na hora da consulta |

Não é preciso instalar Python, Node, Playwright nem Chromium: tudo vem nas imagens. Para rodar sem Docker, veja [Execução sem Docker](#execução-sem-docker).

### 2. Configurar os segredos

O arquivo `backend/.env` guarda a configuração e nunca é versionado. Crie-o a partir do modelo:

```bash
cp backend/.env.example backend/.env
```

Preencha pelo menos a `WAHA_API_KEY`. É uma senha que você mesmo inventa, usada entre o backend e o serviço de WhatsApp:

```bash
openssl rand -hex 32   # copie o resultado para WAHA_API_KEY no backend/.env
```

Opcionalmente, defina `WHATSAPP_DESTINATARIO` com o número que vai receber os relatórios (DDD + 9 + 8 dígitos, com ou sem 55). Sem ele, o painel pede o número a cada consulta.

As demais variáveis estão em [Configuração](#configuração).

### 3. Só em Mac com Apple Silicon

A imagem padrão do WAHA (o serviço de WhatsApp) só existe para processadores Intel/AMD. Em Macs M1, M2, M3 e seguintes, crie um `.env` **na raiz do projeto**. É outro arquivo, diferente do `backend/.env`, e o Docker Compose o lê sozinho:

```bash
echo "WAHA_TAG=arm" > .env
```

Sem isso, o `docker compose up` falha com `no matching manifest for linux/arm64/v8`.

### 4. Subir

```bash
docker compose up
```

A primeira vez leva alguns minutos, porque as imagens são baixadas. Sobem três serviços:

| Serviço | Endereço | O que é |
|---|---|---|
| `frontend` | http://localhost:5173 | painel web (React) |
| `backend` | http://localhost:8000 · [docs](http://localhost:8000/docs) | API (FastAPI) com o robô Playwright |
| `waha` | http://localhost:3000 | WhatsApp HTTP API, que envia as mensagens |

### 5. Conectar o WhatsApp

1. Abra **http://localhost:5173**.
2. Ao lado de **Nova consulta**, o cartão **WhatsApp** mostra um QR code.
3. No celular do chip: **WhatsApp → Dispositivos conectados → Conectar dispositivo**, e aponte a câmera para o código.
4. O QR code some e o cartão passa a mostrar **Conectado**.

O QR code vence em cerca de um minuto. Se vencer, o cartão mostra **Desconectado** e o botão **Gerar QR code**. A conexão fica salva num volume Docker, então só é preciso escanear uma vez.

### 6. Gerar o primeiro relatório

1. Confira os parâmetros. Os padrões já são os da Sol Nascente: segmento 4 (motos), Piauí e Maranhão, Consórcio Nacional Honda.
2. Informe o **WhatsApp do destinatário**, se não configurou um padrão.
3. Clique em **Gerar e enviar relatório**.

A primeira abertura do painel leva cerca de **10 segundos**, porque o robô abre o site do BCB para descobrir as data-bases publicadas. Depois disso, o catálogo fica em cache por 6 horas.

### Parar e limpar

```bash
docker compose down                                  # para tudo, mantém os dados
docker volume rm rpa-sol-nascente_waha_sessions      # desconecta o WhatsApp localmente
```

Para desconectar de vez, remova também o dispositivo no celular (**Dispositivos conectados**). O histórico e os arquivos baixados ficam em `backend/data/`.

---

## Configuração

Toda a configuração vem de variáveis de ambiente, lidas pelo `pydantic-settings`. Nenhum segredo fica no código. O modelo comentado é o [`backend/.env.example`](backend/.env.example).

### `backend/.env`

| Variável | Padrão | Descrição |
|---|---|---|
| `WHATSAPP_PROVIDER` | `waha` | `waha` envia de verdade; `fake` só registra a mensagem no log (ensaio sem celular) |
| `WHATSAPP_DESTINATARIO` | — | destinatário padrão. Dado pessoal: fica fora do repositório |
| `WAHA_API_KEY` | — | **segredo.** Chave entre backend e WAHA, enviada no header `X-Api-Key` |
| `WAHA_URL` | `http://localhost:3000` | no Docker é sobrescrita para `http://waha:3000` |
| `WAHA_SESSION` | `default` | sessão do WAHA; a versão gratuita só tem uma |
| `WAHA_DASHBOARD_USERNAME` / `WAHA_DASHBOARD_PASSWORD` | `admin` / — | login do painel próprio do WAHA em `:3000` (opcional) |
| `BCB_BASE_URL` | página de consórcios do BCB | parametrizada para os testes |
| `DATABASE_URL` | `sqlite:///./data/execucoes.db` | histórico das execuções |
| `DATA_DIR` | `data` | cache dos ZIPs baixados |
| `CATALOGO_TTL_HORAS` | `6` | validade do cache da lista de data-bases |
| `PLAYWRIGHT_HEADLESS` | `true` | `false` abre a janela do navegador (só fora do Docker) |
| `LOG_LEVEL` | `INFO` | nível do log estruturado |

### `.env` na raiz

| Variável | Padrão | Descrição |
|---|---|---|
| `WAHA_TAG` | `latest` | tag da imagem do WAHA; `arm` em Apple Silicon |

---

## Usando o painel

| Área | O que faz |
|---|---|
| **Nova consulta** | data-base, segmento, administradora, praças (UFs), número de concorrentes e destinatário |
| **WhatsApp** | status da conexão; QR code enquanto espera a leitura; **Gerar QR code** quando vence |
| **Acompanhamento** | etapas da execução em tempo real, dados encontrados e a mensagem como aparece no WhatsApp |
| **Histórico** | todas as execuções; clique numa linha para rever os dados e a mensagem |

As opções de data-base e de administradora não são fixas no código: vêm do catálogo que a própria página do BCB publica. Quando o BCB publica um mês novo, ele aparece no painel.

### Ciclo de vida de uma execução

```
PENDENTE → COLETANDO → PROCESSANDO → MENSAGEM_GERADA → ENVIANDO → ENVIADO
               │            │                                 │
               ▼            ▼                                 ▼
         FALHA_COLETA  FALHA_PROCESSAMENTO               FALHA_ENVIO
                            │
                            └──→ SEM_RESULTADO   (desfecho válido: nada a enviar)
```

Uma execução que falhou pode ser repetida: basta clicar de novo em **Gerar e enviar relatório** com os mesmos parâmetros. A mesma execução volta para `PENDENTE` e soma uma tentativa. Uma execução concluída (`ENVIADO` ou `SEM_RESULTADO`) **não se repete**: o painel avisa que o relatório já foi enviado.

### Exemplo de relatório

Mensagem real, enviada pelo sistema para a consulta padrão: Honda, Piauí e Maranhão, Junho/2026. O `*negrito*` e o `_itálico_` são a formatação do WhatsApp.

```
🏍️ *CONSÓRCIO MOTOS – SEGMENTO 4*
📅 Jun/2026 | Fonte: BCB
🔎 UFs: *MA, PI*
🏢 Adms: *Honda, Yamaha, Tradição, Âncora*

📍 *UFs SELECIONADAS* _(trimestre)_
- Consorciados ativos: *405.181*
- Adesões: *49.675*
- Contemplações: 24.636 (89,9% por lance)
- Taxa de exclusão: 41,6%
- Administradoras atuando: 46

- *MA*: 249.533 ativos | 29.664 adesões | Honda 91,5% → 91,9%
- *PI*: 155.648 ativos | 20.011 adesões | Honda 95,7% → 96,6%

🏢 *ADMINISTRADORAS*
*Honda*
  Nas UFs: share 93,1% carteira / 93,8% adesões (46.601 adesões)
  🇧🇷 Taxa 23,2% | Inad. 11,1% | Contemp./mês 4,2%
  🇧🇷 Vendas mês 107.700 | Crédito pendente 114.655

*Yamaha*
  Nas UFs: share 2,4% carteira / 1,8% adesões (898 adesões)
  🇧🇷 Taxa 19,5% | Inad. 19,2% | Contemp./mês 2,5%
  🇧🇷 Vendas mês 4.472 | Crédito pendente 4.447

*Tradição*
  Nas UFs: share 0,4% carteira / 1,5% adesões (748 adesões)
  🇧🇷 Taxa 24,7% | Inad. 27,8% | Contemp./mês 0,8%
  🇧🇷 Vendas mês 404 | Crédito pendente 47

*Âncora*
  Nas UFs: share 0,4% carteira / 0,9% adesões (456 adesões)
  🇧🇷 Taxa 14,3% | Inad. 11,6% | Contemp./mês 0,7%
  🇧🇷 Vendas mês 2.917 | Crédito pendente 894

⚠️ *ALERTAS*
- 📉 Yamaha perdendo share no MA (3,3% → 2,3%)
- 📈 Tradição ganhando share no MA (0,7% → 2,5%)
- 🔴 Yamaha com inadimplência de 19,2%
- 🔴 Tradição com inadimplência de 27,8%

_🇧🇷 = dado nacional de Jun/2026, o BCB não divulga por UF_
```

As regras de share, alertas e concorrentes estão na [entrada 25 das decisões técnicas](docs/DECISOES-TECNICAS.md#25-regras-do-template-do-relatório).

---

## API

Documentação interativa (Swagger) em **http://localhost:8000/docs**.

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/opcoes` | data-bases publicadas, administradoras, segmentos, UFs e padrões do painel |
| `POST` | `/execucoes` | dispara uma consulta. **202** quando cria ou retenta; **200** quando reaproveita uma execução concluída |
| `GET` | `/execucoes/{id}` | status e resultado de uma execução |
| `GET` | `/execucoes?limite=20` | histórico, da mais recente para a mais antiga |
| `GET` | `/whatsapp/conexao` | situação da conexão (`CONECTADO`, `AGUARDANDO_QR`, `INICIANDO`, `DESCONECTADO`, `INDISPONIVEL`) e QR code |
| `POST` | `/whatsapp/conexao/reconectar` | gera um QR code novo |
| `GET` | `/health` | verificação de vida |

```bash
# dispara com os padrões (segmento 4, PI e MA, Honda, destinatário do .env)
curl -X POST localhost:8000/execucoes -H 'Content-Type: application/json' \
     -d '{"data_base": "202607"}'

curl localhost:8000/execucoes/1    # acompanha
curl localhost:8000/execucoes      # histórico
```

---

## Testes

O projeto foi desenvolvido em **TDD**. Os testes da suíte padrão rodam sem rede e sem navegador, usando ZIPs e JSONs reais do BCB guardados em [`backend/tests/fixtures/`](backend/tests/fixtures/).

```bash
# backend (pytest)
docker compose run --rm backend pytest                  # suíte padrão
docker compose run --rm backend pytest -m integration   # contra o site real do BCB
docker compose run --rm backend ruff check .            # lint

# frontend (Vitest + Testing Library), a partir de frontend/
npm install && npm test
npm run build                                           # checagem de tipos + build
```

| Camada | Como é testada |
|---|---|
| `domain/` | funções puras: cálculo de share, consolidação por UF, montagem da mensagem, máquina de estados |
| `parsing/` | ZIPs reais do BCB. Os números de referência (ex.: Honda com 77,3% nacional e 95,7% no PI) servem de oráculo |
| `api/` | `TestClient` do FastAPI, com fonte e envio falsos |
| `infra/whatsapp` | `httpx.MockTransport` respondendo como o WAHA, com formatos capturados da versão 2026.9.1 |
| `rpa/coletor.py` | testes `@pytest.mark.integration` contra o site real, fora da suíte padrão |
| `frontend/` | Vitest na lógica (etapas, formatação, polling); Testing Library nos componentes, pelo papel de acessibilidade |
| arquitetura | [`test_arquitetura.py`](backend/tests/test_arquitetura.py) falha se `domain/` importar rede, banco ou navegador |

---

## Execução sem Docker

Útil para ver o robô navegando numa janela de verdade (`PLAYWRIGHT_HEADLESS=false`). Requer **Python 3.12+** com [**uv**](https://docs.astral.sh/uv/) e **Node 24**.

```bash
# WhatsApp: o WAHA continua no Docker
docker compose up waha

# backend, a partir de backend/
uv sync
uv run playwright install chromium       # ~150 MB, só na primeira vez
uv run uvicorn app.main:app --reload     # http://localhost:8000

# frontend, a partir de frontend/, em outro terminal
npm install
npm run dev                              # http://localhost:5173 (repassa a API para :8000)
```

No host, `WAHA_URL` fica com o padrão `http://localhost:3000`.

---

## Arquitetura

```
┌──────────────┐   HTTP    ┌───────────────────────────── backend (FastAPI) ─────────────────────────────┐
│  frontend    │ ────────▶ │  api/  ──▶  domain/ (regras puras)  ◀──  infra/ · rpa/ · parsing/           │
│  React + TS  │  polling  │                  │                        │         │          │            │
└──────────────┘           │                  │ portas (Protocol)      │         │          │            │
                           │                  ▼                        ▼         ▼          ▼            │
                           │        FonteDeDados · WhatsAppSender   SQLite   Playwright   CSV/ZIP         │
                           └────────────────────────────────────────────────────┬────────────┬──────────┘
                                                                                ▼            ▼
                                                                        site do BCB      WAHA → WhatsApp
```

**Direção da dependência: `api → domain → infra`.** O `domain/` não importa Playwright, SQLAlchemy nem `httpx`, e um teste garante isso. Integrações externas entram por `Protocol` definido no domínio e implementado em `infra/`. É assim que o envio tem um adapter real (`WahaSender`) e um falso (`FakeSender`), trocados por uma variável de ambiente.

```
backend/app/
  api/        rotas FastAPI e schemas de entrada e saída
  domain/     execução e máquina de estados, análise, montagem da mensagem, portas
  rpa/        Playwright: catálogo (função pura) e coletor (navegação e download)
  parsing/    unzip, leitura dos CSVs em windows-1252, normalização
  infra/      SQLite, adapters de WhatsApp, cache, logging
  config.py   configuração (pydantic-settings)
backend/tests/fixtures/   ZIPs e JSONs reais do BCB (versionados)
frontend/src/             api/ · dominio/ · hooks/ · componentes/
docs/                     PRD, ADRs e registro de decisões técnicas
```

| Camada | Tecnologia | Por quê ([ADR-001](docs/adr/ADR-001-stack-e-arquitetura.md)) |
|---|---|---|
| Robô | Playwright (Chromium) | a página do BCB é uma SPA Angular: sem browser real não há dado |
| API | Python + FastAPI | o ecossistema de dados e de RPA está em Python; documentação automática |
| Persistência | SQLite + SQLAlchemy | um usuário e dezenas de registros; migrar para Postgres é trocar a URL |
| Painel | React + TypeScript (Vite) | estado de acompanhamento em tempo real; sem biblioteca de componentes |
| WhatsApp | WAHA | envio real sem burocracia, só para demonstração ([ADR-009](docs/adr/ADR-009-waha-para-demonstracao.md)) |
| Empacotamento | Docker Compose | a avaliação roda sem instalar Python, Node nem Chromium |

---

## Como o desafio foi atendido

| Exigência | Como | Detalhes |
|---|---|---|
| **Acessar e navegar no sistema público** | Playwright abre a página Angular do BCB, recusa os cookies, escolhe a data-base no `ng-select` e clica em "Baixar arquivo" | [ADR-002](docs/adr/ADR-002-fonte-bcb-e-estrategia-de-rpa.md) |
| **Estratégia de extração** | o robô lê a lista de arquivos na resposta de rede que a própria página pede. Nenhuma URL ou GUID interno fica fixo no código. A página ASP legada, que responde a `curl`, foi descartada porque está **~2 meses defasada** | [ADR-002](docs/adr/ADR-002-fonte-bcb-e-estrategia-de-rpa.md), [ADR-008](docs/adr/ADR-008-catalogo-pela-rede-da-pagina.md) |
| **Tratamento dos dados** | CSV em `windows-1252`, separador `;`, decimal com vírgula; `strip()` nos nomes com espaços; CNPJ mantido como texto com zeros à esquerda; cruzamento do dataset mensal com o trimestral | [ADR-002](docs/adr/ADR-002-fonte-bcb-e-estrategia-de-rpa.md) |
| **Consulta sem resultado** | termina em `SEM_RESULTADO`, registra o motivo e **não envia** | [PRD §7](docs/PRD.md) |
| **Informações incompletas** | campo numérico ausente ou ilegível vira zero; mês sem arquivo por UF usa o trimestre mais recente e o relatório informa a data-base de cada bloco | [PRD §7](docs/PRD.md) |
| **Indisponibilidade e falha na navegação** | timeouts do Playwright e erros de download viram `ColetaError` → `FALHA_COLETA` com a descrição, sem vazar exceção de biblioteca | [DT-22](docs/DECISOES-TECNICAS.md#22-processar-nunca-deixa-exceção-escapar) |
| **Mensagem personalizada** | gerada a partir dos números apurados: praças, share, concorrentes e alertas | [DT-25](docs/DECISOES-TECNICAS.md#25-regras-do-template-do-relatório) |
| **Integração com WhatsApp** | WAHA, com adapter trocável por variável de ambiente; QR code e status no painel | [ADR-009](docs/adr/ADR-009-waha-para-demonstracao.md) |
| **Processamento ou envio duplicado** | hash SHA-256 dos parâmetros com **unique constraint** no banco: concluída não repete, em andamento não duplica, falha pode ser retentada. Os ZIPs ficam em cache com revalidação por `ETag` | [ADR-004](docs/adr/ADR-004-persistencia-e-idempotencia.md), [ADR-006](docs/adr/ADR-006-estrategia-de-cache-e-revalidacao.md) |
| **Histórico e rastreabilidade** | parâmetros, dados encontrados, data e hora, destinatário, mensagem, status, id da mensagem no WhatsApp, tipo e descrição do erro | [ADR-004](docs/adr/ADR-004-persistencia-e-idempotencia.md) |
| **Erros e logs** | exceções de domínio (`ColetaError`, `ParsingError`, `EnvioError`); log em JSON no stdout com `execucao_id` em toda linha | [ADR-001](docs/adr/ADR-001-stack-e-arquitetura.md) |
| **Credenciais fora do código** | `.env` fora do git, só o `.env.example` é versionado. Chaves mascaradas no log, no `repr` dos adapters e nas mensagens de erro | [ADR-005](docs/adr/ADR-005-configuracao-e-segredos.md) |

Para acompanhar os logs de uma execução:

```bash
docker compose logs -f backend
```

---

## Solução de problemas

| Sintoma | Causa e solução |
|---|---|
| `no matching manifest for linux/arm64/v8` ao subir | Mac com Apple Silicon: crie o `.env` da raiz com `WAHA_TAG=arm` ([passo 3](#3-só-em-mac-com-apple-silicon)) |
| Cartão WhatsApp **Desconectado** | o QR code venceu sem leitura, ou o celular removeu o dispositivo. Clique em **Gerar QR code** |
| Cartão WhatsApp **Indisponível** | o container `waha` não subiu: `docker compose ps` e `docker compose logs waha` |
| Envio falha com "API key do WAHA inválida" | a `WAHA_API_KEY` mudou depois de o container subir: `docker compose up -d --force-recreate waha backend` |
| Envio falha com "o número … não tem WhatsApp" | o destinatário não tem conta no WhatsApp; confira DDD e número |
| Painel demora ~10 s ao abrir | esperado na primeira carga: o robô está lendo o catálogo do BCB |
| Execução em `FALHA_COLETA` | site do BCB fora do ar ou lento. A descrição do erro aparece no acompanhamento; tente de novo depois |
| Quero ensaiar sem celular | `WHATSAPP_PROVIDER=fake` no `backend/.env` e `docker compose restart backend`: a mensagem vai só para o log e para o painel |

---

## Limitações e caminho para produção

O projeto foi feito para **demonstração**. O que mudaria para produção:

- **WhatsApp oficial.** O WAHA não é oficial: automatizar o WhatsApp fora da API da Meta viola os termos de uso, e o número pode ser banido. Em produção, o caminho é a WhatsApp Business Cloud API, com número comercial verificado, token de System User, template aprovado ou janela de 24 horas, e webhook de status de entrega. Basta implementar mais um adapter do `WhatsAppSender`, sem tocar no domínio. Roteiro completo no [ADR-009](docs/adr/ADR-009-waha-para-demonstracao.md#caminho-para-produção).
- **Execução em fila.** Hoje a coleta roda em `BackgroundTasks` do FastAPI, no mesmo processo. Com vários usuários ou agendamento, o certo seria uma fila (Celery/RQ ou um job agendado) e um processo que retome execuções órfãs.
- **Agendamento.** Disparar o relatório sozinho quando o BCB publica um trimestre novo, em vez de depender de um clique.
- **Banco e armazenamento.** PostgreSQL no lugar do SQLite (a troca é de connection string) e expurgo do cache de ZIPs, que cresce sem limite.
- **Segurança.** Autenticação no painel e na API, que hoje são abertos. Portas publicadas só em `127.0.0.1` ou atrás de um proxy com TLS. Segredos num cofre, no lugar do `.env`.
- **Observabilidade.** Os logs já são JSON com `execucao_id`; faltam métricas e alertas para falhas de coleta, porque o layout do BCB pode mudar a qualquer momento.

---

## Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | problema, usuário, fonte de dados, parâmetros, relatório e regras de negócio |
| [`docs/adr/`](docs/adr/README.md) | decisões de arquitetura: stack, fonte e RPA, persistência, segredos, cache, Docker, catálogo e WhatsApp |
| [`docs/DECISOES-TECNICAS.md`](docs/DECISOES-TECNICAS.md) | registro das escolhas menores, cada uma com a alternativa rejeitada e o motivo |
| [`CLAUDE.md`](CLAUDE.md) | padrões de código, estratégia de testes e armadilhas já verificadas da fonte BCB |

### WhatsApp: por que um chip dedicado

O WAHA conecta um número de WhatsApp comum, como o WhatsApp Web. Tudo roda na sua máquina, sem servidor de terceiros, e o projeto só usa duas operações: verificar se o número existe e enviar texto. Ainda assim, enquanto conectado, o WAHA teria acesso às conversas daquele número, e automação não oficial pode levar a banimento. Por isso: **use um chip só para isso, nunca o seu número pessoal nem o da concessionária.**
