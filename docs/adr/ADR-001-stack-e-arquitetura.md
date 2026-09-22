# ADR-001 — Stack e arquitetura

**Status:** Aceito · 2026-09-22

## Contexto

O projeto precisa reunir quatro capacidades bem diferentes: automação de browser, parsing de arquivos CSV governamentais mal formatados, uma API com execução assíncrona e uma interface web. O enunciado não obriga nenhuma tecnologia, mas cobra justificativa para a escolha.

Duas restrições práticas pesaram na decisão: a solução será **apresentada ao vivo**, então cada peça a mais é um ponto a mais de falha na demonstração; e a vaga é de desenvolvedor **full stack**, então a interface não pode ser um detalhe escondido.

## Decisão

**Backend em Python**, com Playwright para o RPA, FastAPI para a API e SQLite via SQLAlchemy para persistência.
**Frontend em React + TypeScript** com Vite, consumindo a API por HTTP.

O build do frontend é servido como arquivo estático pelo próprio FastAPI, de modo que a aplicação inteira sobe com **um único comando** em produção/demo. Em desenvolvimento, o Vite roda em separado com proxy para a API.

Organização em camadas, dentro de `backend/app/`:

```
api/       rotas FastAPI, schemas de entrada e saída
domain/    entidades, regras de negócio, montagem do relatório
rpa/       Playwright: navegação e download
parsing/   descompactação, leitura de CSV, normalização
infra/     SQLAlchemy, adapters de WhatsApp, logging
config.py  pydantic-settings
```

A regra de dependência é `api → domain → infra`. O pacote `domain` é **puro**: não importa Playwright, SQLAlchemy nem cliente HTTP. Toda a lógica de cálculo de share, consolidação por UF e composição da mensagem é testável sem rede e sem banco.

## Justificativa

O gargalo real deste projeto não é a interface nem a API — é automatizar um formulário ASP legado e domar arquivos CSV em `windows-1252` com decimal por vírgula. É aí que o ferramental Python é mais direto: `zipfile` na biblioteca padrão, leitura de CSV com encoding e separador declarados em uma linha, e um ecossistema de RPA que é a convenção do mercado brasileiro para esse tipo de trabalho.

A escolha de React em vez de renderização no servidor foi deliberada: o painel tem multi-seleção de UF, multi-seleção de métricas e acompanhamento do status da execução em tempo real. Um formulário server-rendered daria conta, mas a vaga é full stack e a interface é a parte visível do trabalho.

A execução do RPA leva dezenas de segundos, então a rota que dispara a consulta retorna imediatamente com um `execucao_id` e agenda o trabalho em `BackgroundTasks` do FastAPI. O frontend acompanha por polling. Isso evita introduzir Celery, Redis ou qualquer worker externo — infraestrutura que não se justifica no volume deste produto e que seria mais uma peça para subir na apresentação.

## Consequências

**Positivas** — o domínio isolado permite testar as regras de negócio sem browser e sem rede. Um comando só para subir tudo reduz o risco na demonstração. Dois runtimes em desenvolvimento, mas um único artefato no fim.

**Negativas** — são duas toolchains para instalar (`pip` e `npm`), o que alonga o README. `BackgroundTasks` roda no mesmo processo do servidor: se o processo cair no meio de uma execução, ela fica órfã em estado intermediário. Aceitável para o escopo; em produção seria um worker separado com fila durável, e a máquina de estados em [ADR-004](ADR-004-persistencia-e-idempotencia.md) já permite retomar execuções travadas.

## Alternativas consideradas

**Next.js, full TypeScript.** Uma linguagem só, um `package.json`, e o Playwright tem Node como linguagem de primeira classe. Descartada porque route handlers do Next não são bons para trabalho longo — exigiria um worker separado de qualquer forma — e porque o tratamento de ZIP e de CSV `cp1252` com decimal vírgula demandaria dependências extras e coerção manual que em Python sai de graça.

**Python com Jinja2 + HTMX.** Menos peças, um runtime só, e daria conta do painel. Descartada por subvender o lado frontend numa vaga de full stack.

**Híbrido com dois serviços independentes.** Mais próximo de produção, porém a pior escolha para uma apresentação ao vivo: dois processos para subir e explicar, sem benefício nesta escala.
