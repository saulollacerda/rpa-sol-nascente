# Registro de decisões técnicas

Log corrente das escolhas técnicas do projeto e do raciocínio por trás delas.

**Diferença para os [ADRs](adr/):** os ADRs são documentos formais, poucos e estáveis — uma decisão arquitetural estruturada por arquivo. Este registro é mais granular e mais didático: inclui comparações conceituais, escolhas pequenas de implementação e as alternativas que foram descartadas. Serve principalmente de material para defender as decisões na apresentação final, que é critério explícito de avaliação do desafio.

Cada entrada traz a alternativa rejeitada, o motivo real e uma frase curta de defesa.

| # | Decisão | ADR |
|---|---|---|
| [1](#1-playwright-em-vez-de-scraping-http) | Playwright em vez de scraping HTTP | [002](adr/ADR-002-fonte-bcb-e-estrategia-de-rpa.md) |
| [2](#2-o-projeto-é-rpa-não-web-scraping) | O projeto é RPA, não web scraping | — |
| [3](#3-página-angular-em-vez-da-página-asp-legada) | Página Angular em vez da ASP legada | [002](adr/ADR-002-fonte-bcb-e-estrategia-de-rpa.md) |
| [4](#4-navegar-o-dropdown-em-vez-de-montar-a-url-do-zip) | Navegar o dropdown em vez de montar a URL | [002](adr/ADR-002-fonte-bcb-e-estrategia-de-rpa.md) |
| [5](#5-python-no-backend-em-vez-de-typescript) | Python no backend | [001](adr/ADR-001-stack-e-arquitetura.md) |
| [6](#6-react-em-vez-de-renderização-no-servidor) | React em vez de server-rendered | [001](adr/ADR-001-stack-e-arquitetura.md) |
| [7](#7-backgroundtasks-em-vez-de-celery) | BackgroundTasks em vez de Celery | [001](adr/ADR-001-stack-e-arquitetura.md) |
| [8](#8-build-do-react-servido-pelo-fastapi) | Build do React servido pelo FastAPI | [001](adr/ADR-001-stack-e-arquitetura.md) |
| [9](#9-sqlite-em-vez-de-postgresql) | SQLite em vez de PostgreSQL | [004](adr/ADR-004-persistencia-e-idempotencia.md) |
| [10](#10-hash-de-parâmetros-em-vez-de-comparação-campo-a-campo) | Hash de parâmetros para idempotência | [004](adr/ADR-004-persistencia-e-idempotencia.md) |
| [11](#11-cache-dos-zips-baixados) | Cache dos ZIPs baixados | [004](adr/ADR-004-persistencia-e-idempotencia.md) |
| [12](#12-cloud-api-da-meta-em-vez-de-twilio-ou-baileys) | Cloud API da Meta para WhatsApp | [003](adr/ADR-003-integracao-whatsapp.md) |
| [13](#13-adapter-fake-de-whatsapp-ao-lado-do-real) | Adapter fake ao lado do real | [003](adr/ADR-003-integracao-whatsapp.md) |
| [14](#14-baixar-os-dois-datasets-consolidado-e-uf) | Baixar os dois datasets | [002](adr/ADR-002-fonte-bcb-e-estrategia-de-rpa.md) |
| [15](#15-pydantic-settings-em-vez-de-osenviron) | pydantic-settings em vez de `os.environ` | [005](adr/ADR-005-configuracao-e-segredos.md) |
| [16](#16-domínio-puro-sem-io) | Domínio puro, sem I/O | [001](adr/ADR-001-stack-e-arquitetura.md) |
| [17](#17-desenvolvimento-guiado-por-testes-tdd) | Desenvolvimento guiado por testes (TDD) | — |
| [18](#18-cachear-o-catálogo-e-não-só-o-arquivo) | Cachear o catálogo, e não só o arquivo | [006](adr/ADR-006-estrategia-de-cache-e-revalidacao.md) |
| [19](#19-escutar-a-rede-da-página-em-vez-de-chamar-a-api) | Escutar a rede da página em vez de chamar a API | [008](adr/ADR-008-catalogo-pela-rede-da-pagina.md) |

---

## 1. Playwright em vez de scraping HTTP

**Alternativa rejeitada:** `requests` + `BeautifulSoup`.

Scraping por HTTP é muito mais rápido (milissegundos contra segundos) e não exige baixar ~150 MB de navegador. A regra sensata é usar HTTP sempre que der e recorrer a browser só quando não der.

Aqui não dá. A página do BCB é uma aplicação Angular: testamos e um `GET` na URL oficial retorna **2.871 bytes e nenhum dado**. Com `requests` você recebe uma casca HTML vazia — não é que extrair seria difícil, é que não há conteúdo para extrair. Além disso o seletor de data-base é um `ng-select`, não um `<form>` nativo, então também não existe formulário para submeter via POST.

> **Em uma frase:** não foi preferência — o conteúdo é montado por JavaScript, então sem navegador não há nada para ler nem com o que interagir.

## 2. O projeto é RPA, não web scraping

**Distinção conceitual**, não escolha de ferramenta.

Web scraping é extrair dados de dentro do HTML: pegar preços de uma `<table>`, títulos de `<div>`s. O nosso fluxo não faz isso. O navegador serve para **chegar até um arquivo**, não para extrair informação da página:

```
Playwright  → navega e baixa um ZIP      (automação de browser)
zipfile     → descompacta
csv         → lê os CSVs                 (parsing de arquivo)
```

O dado nunca está no HTML — está em CSVs dentro de um ZIP.

Isso tem consequência arquitetural real: se o BCB mudar o layout do site, o parser não quebra, só a camada de navegação precisa de ajuste. É por isso que `rpa/` e `parsing/` são pacotes separados — falham por causas diferentes.

> **Em uma frase:** RPA é imitar um humano operando um sistema; scraping é extrair dado de páginas. Aqui o dado vem estruturado em CSV, o que é bem mais confiável que HTML raspado.

## 3. Página Angular em vez da página ASP legada

**Alternativa rejeitada:** automatizar `consorcio_banco_de_dados.asp`, que tem `<select>` nativo e responde a `curl`.

Seria muito mais simples. É uma armadilha: o ASP está **defasado em cerca de dois meses** e serve arquivos de outro diretório.

| | ASP legado | Página atual |
|---|---|---|
| Consolidado | Maio/2026 | **Julho/2026** |
| Por UF | Março/2026 | **Junho/2026** |
| Diretório | `/Fis/Consorcios/Port/BD/` | `/content/estabilidadefinanceira/consorcio-banco-de-dados/` |

Confirmado que não é cache: um fetch com `Cache-Control: no-cache` retornou `x-cache: TCP_MISS` e ainda assim listava Maio/2026.

Automatizar o ASP entregaria dado velho **sem erro nenhum** — a pior classe de falha, porque é silenciosa e plausível. Por isso o sistema nunca afirma qual data-base tem: ele reporta a que efetivamente coletou.

> **Em uma frase:** existiam duas fontes parecidas e a mais fácil de automatizar estava desatualizada — descobrir isso mudou o alvo da automação.

## 4. Navegar o dropdown em vez de montar a URL do ZIP

**Alternativa rejeitada:** conhecendo o padrão `/content/.../dados-consolidados/AAAAMMConsorcios.zip`, baixar direto por HTTP.

Seria muito mais rápido e dispensaria o navegador. Rejeitado porque equivale a hardcodar a URL de download. O BCB acabou de migrar do ASP para o CMS, mudando todo o esquema de diretórios — se fizer de novo, a automação quebra em silêncio ou, pior, continua baixando de um caminho antigo que ainda responde.

Ler as opções que a página oferece sobrevive a esse tipo de migração. As data-bases disponíveis são lidas do `ng-select` em tempo de execução, nunca hardcoded.

> **Em uma frase:** montar a URL na mão é rápido até o dia em que o órgão reorganiza o site — o que acabou de acontecer.

## 5. Python no backend em vez de TypeScript

**Alternativa rejeitada:** Next.js com TypeScript no back e no front.

Uma linguagem só seria mais enxuto. Mas o gargalo real do projeto não é a API nem a interface — é automatizar um site legado e domar CSV governamental mal formatado. É aí que Python é mais direto: `zipfile` na biblioteca padrão, leitura de CSV com encoding e separador declarados em uma linha, e um ecossistema de RPA que é a convenção do mercado brasileiro.

Em Node, o mesmo trabalho exigiria `adm-zip`, `iconv-lite` e coerção manual do decimal por vírgula.

> **Em uma frase:** escolhi pela natureza do gargalo, que é automação e parsing, não pela conveniência de ter uma linguagem só.

## 6. React em vez de renderização no servidor

**Alternativa rejeitada:** Jinja2 + HTMX.

Server-rendered daria conta e teria menos peças. Optamos por React porque o painel tem multi-seleção de UF, multi-seleção de métricas e acompanhamento do status da execução em tempo real — e porque a vaga é full stack, então a interface é a parte visível do trabalho.

> **Em uma frase:** o enunciado permite interface simples, mas simples não precisa significar pobre.

## 7. BackgroundTasks em vez de Celery

**Alternativa rejeitada:** Celery + Redis, ou um worker dedicado.

A coleta leva dezenas de segundos, então a requisição não pode ser síncrona. A rota que dispara a consulta retorna na hora com um `execucao_id` e agenda o trabalho em `BackgroundTasks` do FastAPI; o frontend acompanha por polling.

Celery resolveria melhor, mas exigiria Redis e um processo a mais — infraestrutura desproporcional ao volume real (um usuário, execuções manuais) e mais uma peça para subir na apresentação.

**Limitação assumida:** roda no mesmo processo do servidor, então uma queda deixa a execução órfã em estado intermediário. A máquina de estados do [ADR-004](adr/ADR-004-persistencia-e-idempotencia.md) permite detectar essas execuções.

> **Em uma frase:** fila durável é o certo em produção, mas aqui seria infraestrutura sem demanda — e a máquina de estados já deixa o caminho aberto.

## 8. Build do React servido pelo FastAPI

Em desenvolvimento, Vite e FastAPI rodam separados, com proxy. Em produção e na demonstração, o build do React é servido como arquivo estático pelo próprio FastAPI.

O motivo é reduzir risco: a solução será apresentada ao vivo, e um comando só para subir tudo é bem menos frágil que dois processos coordenados.

> **Em uma frase:** dois runtimes em desenvolvimento, um artefato só no fim.

## 9. SQLite em vez de PostgreSQL

**Alternativa rejeitada:** PostgreSQL via Docker.

A escala real é um usuário, execuções manuais, dezenas de registros. SQLite não exige serviço para subir, o banco inteiro é um arquivo, e via SQLAlchemy migrar para PostgreSQL seria trocar a connection string.

**Limitação assumida:** não suporta escrita concorrente de verdade. Irrelevante neste uso.

> **Em uma frase:** escolhi pela escala real do produto, e o ORM mantém a porta aberta.

## 10. Hash de parâmetros em vez de comparação campo a campo

O enunciado exige controle contra processamento e envio duplicado. Em vez de comparar parâmetro por parâmetro em cada caminho de código, cada execução carrega um `parametros_hash`:

```
sha256( data_base | segmento | ufs_ordenadas | administradoras_ordenadas
        | metricas_ordenadas | destinatario )
```

com **unique constraint** na coluna. A regra passa a ser garantida pelo banco, não pela disciplina do programador.

Dois detalhes que importam: a **ordenação das coleções é obrigatória**, senão `[PI, MA]` e `[MA, PI]` gerariam hashes diferentes para a mesma consulta; e o **destinatário entra na chave**, porque o mesmo relatório para outra pessoa é envio legítimo, não duplicata.

> **Em uma frase:** reduzi a regra a uma constraint no banco, que é impossível de esquecer em algum caminho de código.

## 11. Cache dos ZIPs baixados

Os arquivos são guardados em `data/` nomeados pela data-base. Uma execução que precise de uma data-base já baixada reaproveita o arquivo.

Serve a três propósitos ao mesmo tempo: torna a demonstração rápida na segunda execução, reduz carga sobre um serviço público, e é a segunda camada de defesa contra reprocessamento.

**Limitação assumida:** o diretório cresce indefinidamente, sem expurgo no MVP.

> **Em uma frase:** bater de novo num serviço público para buscar um arquivo que já tenho é desperdício em três frentes.

## 12. Cloud API da Meta em vez de Twilio ou Baileys

**Alternativas rejeitadas:** Twilio WhatsApp Sandbox e whatsapp-web.js / Baileys.

Twilio seria mais rápido de configurar, mas introduz um intermediário pago no caminho. A pergunta "como isso vira produção?" se responde melhor apontando para o canal oficial do que para um revendedor.

Baileys e whatsapp-web.js automatizam a sessão do WhatsApp Web via QR code, com custo zero. Descartadas por **violarem os termos de uso da Meta** — o número pode ser banido — e por dependerem de engenharia reversa de um protocolo não documentado, quebrando a cada mudança do WhatsApp Web. Recomendar isso a um cliente real seria irresponsável.

> **Em uma frase:** é o único caminho que uma concessionária poderia de fato levar para produção sem risco de ter o número banido.

## 13. Adapter fake de WhatsApp ao lado do real

`WhatsAppSender` é um `Protocol` com duas implementações: `CloudApiSender` e `FakeSender`, escolhidas por `WHATSAPP_PROVIDER`.

O fake não é atalho, é desenho. Resolve três coisas: permite testar o fluxo completo sem rede nem consumo de cota; garante que a apresentação ao vivo não quebre por token expirado ou rate limit; e força a fronteira de abstração a ser real, porque duas implementações concretas provam que o domínio não vazou detalhe de infraestrutura.

> **Em uma frase:** ter duas implementações é o que prova que a abstração existe de verdade.

## 14. Baixar os dois datasets, consolidado e UF

**Alternativa rejeitada:** usar só um deles.

As métricas relevantes estão divididas e não há sobreposição:

| Dataset | Periodicidade | Exclusivo dele |
|---|---|---|
| Consolidado | mensal | taxa de administração, inadimplência, grupos ativos |
| Por UF | trimestral | recorte geográfico, adesões, contemplação por lance vs sorteio |

Usar só o consolidado perderia o corte por UF, que é justamente o que interessa a uma concessionária. Usar só o de UF perderia taxa e inadimplência, e ficaria com dado trimestral em vez de mensal.

São dois parsers atrás de uma interface comum. Como as data-bases não coincidem, o relatório informa a de cada bloco em vez de assumir uma só.

> **Em uma frase:** o painel promete deixar o usuário escolher os parâmetros disponíveis nos CSV, e cumprir isso exige os dois arquivos.

## 15. pydantic-settings em vez de `os.environ`

**Alternativa rejeitada:** `python-dotenv` puro, ou ler `os.environ` direto onde precisa.

`pydantic-settings` valida tipo e presença na subida do processo. A diferença prática é entre um erro claro ao iniciar e um `None` silencioso que só estoura três camadas abaixo — depois de já ter baixado os arquivos.

Nenhum módulo lê `os.environ` diretamente: todo acesso passa pelo objeto `Settings`, o que dá um único lugar para auditar o que o sistema consome. O sistema **falha na inicialização** se o provider for `cloud_api` e o token estiver ausente.

> **Em uma frase:** falhar cedo e explicitamente vale mais que descobrir a credencial faltando no meio da execução.

## 16. Domínio puro, sem I/O

A direção da dependência é `api → domain → infra`, e `domain/` não importa Playwright, SQLAlchemy nem cliente HTTP.

Não é purismo: é o que torna as regras de negócio — cálculo de share, consolidação por UF, composição da mensagem — testáveis sem rede, sem browser e sem banco. Numa solução cujo caminho feliz leva dezenas de segundos e depende de um site de terceiro, poder testar a lógica em milissegundos é a diferença entre ter testes e não ter.

Integrações externas entram por `Protocol` definido no domínio e implementado em `infra/`.

> **Em uma frase:** separei o que depende do mundo externo do que não depende, para poder testar a lógica sem depender do BCB estar no ar.

## 17. Desenvolvimento guiado por testes (TDD)

**Alternativa rejeitada:** escrever o código primeiro e os testes depois, se sobrar tempo.

O desenvolvimento segue o ciclo *red-green-refactor*: escreve-se um teste que falha, o código mínimo que o faz passar, e só então se refatora. A ferramenta é `pytest`.

O ponto que exige honestidade é **onde TDD se aplica**. Boa parte deste projeto conversa com um site de terceiro, e escrever teste-primeiro contra um site do governo não é TDD — é teatro. O escopo é explícito:

| Camada | Teste primeiro? | Como |
|---|---|---|
| `domain/` | ✅ sempre | funções puras: share, consolidação por UF, composição da mensagem |
| `parsing/` | ✅ sempre | fixture ZIP versionado em `backend/tests/fixtures/` |
| `api/` | ✅ sempre | `TestClient` do FastAPI |
| `infra/whatsapp` | ✅ sempre | via `FakeSender` |
| `infra/db` | ⚠️ parcial | SQLite em memória; migrações não se testam antes |
| `rpa/` | ❌ não | site externo, lento e não-determinístico |

Para o `rpa/`, a abordagem é outra: um **spike exploratório descartável** para descobrir os seletores reais, jogado fora depois, e então um adapter fino coberto por teste de integração marcado (`@pytest.mark.integration`), que não roda na suíte padrão. O que é testável ali é o contrato — dado um ZIP, o que a camada devolve — e isso já está coberto por `parsing/`.

### Consequências práticas

**A ordem de trabalho muda.** O plano anterior começava pelo Playwright, por ser a parte mais arriscada. Com TDD, o caminho passa a ser: `parsing/` primeiro (test-first, usando um ZIP já baixado), depois `domain/`, e o `rpa/` só então — precedido por um spike. O risco da coleta continua sendo endereçado cedo, mas pelo spike, não pelo código definitivo.

**Já existe oráculo de teste.** Os números de referência apurados da fonte e registrados no [`CLAUDE.md`](../CLAUDE.md) — Honda 77,3% nacional, PI 95,7%, MA 91,5%, 750 e 7.667 linhas — são assertivas prontas. O parser tem gabarito antes da primeira linha de código.

**Fixtures são versionadas.** Ficam em `backend/tests/fixtures/`, não em `data/`, que é ignorado pelo git. Confundir os dois quebraria a suíte em qualquer máquina que não a original.

**Reforça uma decisão anterior.** O domínio puro da entrada [16](#16-domínio-puro-sem-io) deixa de ser preferência estética e passa a ser pré-requisito: só dá para escrever teste antes do código se o código não depender de rede, browser e banco.

> **Em uma frase:** testo primeiro onde o resultado é determinístico, e onde não é — a navegação no site do BCB — uso spike e teste de integração marcado, em vez de fingir que dá para fazer TDD contra um site de terceiro.

## 18. Cachear o catálogo, e não só o arquivo

**Alternativa rejeitada:** cachear apenas os ZIPs baixados, como o ADR-004 previa originalmente.

A pergunta que expôs o problema foi prática: se o gestor consultar sempre a data-base mais recente, baixa tudo de novo toda vez? Medindo, a intuição estava invertida:

| Etapa | Custo |
|---|---|
| Playwright: browser, navegação, leitura do `ng-select` | **~10–20s** |
| Download do ZIP | 1,25s |
| Unzip e parse de 7.667 linhas | milissegundos |

O download é ~6% do tempo. Cachear só o artefato economizaria a parte barata e manteria a espera de 20 segundos em toda consulta repetida.

A correção é cachear também o **catálogo** — a lista de data-bases e a URL de cada arquivo, com TTL de 6 horas. Com ele válido, o sistema já sabe a URL e não precisa navegar para descobri-la: a consulta repetida cai para menos de 1 segundo, sem abrir o browser.

### O cache permanente estaria errado

O BCB declara que *"a cada data-base são atualizadas as informações relativas aos últimos 12 períodos"* — arquivos publicados são revisados. Cache eterno serviria dado velho sem erro, a mesma falha silenciosa da armadilha do ASP na entrada [3](#3-página-angular-em-vez-da-página-asp-legada).

Testado contra o servidor:

```
If-None-Match      →  HTTP 304, 0 bytes         ✅
If-Modified-Since  →  HTTP 200, 108.814 bytes   ❌
```

`ETag` funciona, `Last-Modified` não. E a data engana: o arquivo de Set/2024 reporta modificação em agosto de 2026, que é a data da migração de CMS do BCB, não revisão de conteúdo.

### Não contradiz a entrada 4

Pular o browser parece contrariar a decisão de [não montar a URL do ZIP](#4-navegar-o-dropdown-em-vez-de-montar-a-url-do-zip). Não é o mesmo caso: a URL **vem do catálogo que o browser leu**, não de um padrão de nome inventado. O navegador segue sendo a única fonte de URLs; o cache só evita repetir a navegação enquanto o catálogo estiver fresco.

> **Em uma frase:** medi antes de otimizar e descobri que o cache que eu tinha desenhado economizava 6% do tempo — o que precisava ser cacheado era a navegação, não o download.

## 19. Escutar a rede da página em vez de chamar a API

**Alternativas rejeitadas:** ler o texto do dropdown, e chamar a API interna do BCB diretamente.

O spike contra o site real mostrou que a página não traz a lista de arquivos no HTML: ela pede a uma API JSON interna, que devolve nome, tamanho, data de publicação e **URL** de cada arquivo. O texto do dropdown só dá nome e tamanho, e a URL — de que o cache da entrada [18](#18-cachear-o-catálogo-e-não-só-o-arquivo) precisa — só aparece depois do download.

Chamar a API direto seria oito vezes mais rápido. Mas obrigaria a fixar no código um endpoint não documentado e um `guid` opaco: o mesmo risco rejeitado na entrada [4](#4-navegar-o-dropdown-em-vez-de-montar-a-url-do-zip).

A saída foi navegar normalmente e **escutar** as respostas que a própria página faz. O navegador continua sendo a única fonte; o robô só lê o que a página pediu, seja qual for o endereço. Os itens são classificados pelo padrão do nome do arquivo, dependência que o parser já tinha.

> **Em uma frase:** o spike mostrou que a página já pedia os dados estruturados que eu precisava — em vez de copiar o endereço dela, passei a escutar o que ela pede.
