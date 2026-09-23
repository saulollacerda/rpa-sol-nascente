# Architecture Decision Records

Registro das decisões de arquitetura do projeto. Um ADR documenta **uma** decisão relevante: o contexto em que foi tomada, o que se decidiu, o que isso custa e quais alternativas foram descartadas.

A motivação é prática. Decisões de arquitetura são difíceis de reconstruir depois — o código mostra o *que* foi feito, nunca o *porquê*, nem o que se considerou e rejeitou. Neste projeto há uma razão adicional: o desafio avalia explicitamente a *"capacidade de explicar e justificar as decisões técnicas"*.

## Índice

| # | Decisão | Resumo |
|---|---|---|
| [001](ADR-001-stack-e-arquitetura.md) | Stack e arquitetura | Python + FastAPI no back, React + Vite no front, organizado em camadas com domínio puro |
| [002](ADR-002-fonte-bcb-e-estrategia-de-rpa.md) | Fonte BCB e estratégia de RPA | Playwright contra a página Angular — nunca contra o ASP legado, que está defasado |
| [003](ADR-003-integracao-whatsapp.md) | Integração com WhatsApp | ~~Cloud API oficial da Meta~~ — substituído pelo 009 |
| [004](ADR-004-persistencia-e-idempotencia.md) | Persistência e idempotência | SQLite, hash SHA-256 dos parâmetros sob unique constraint, máquina de estados |
| [005](ADR-005-configuracao-e-segredos.md) | Configuração e segredos | `pydantic-settings` com `.env`, nenhum token no código, falha na inicialização |
| [006](ADR-006-estrategia-de-cache-e-revalidacao.md) | Estratégia de cache e revalidação | Cache em três camadas; revalidação por `ETag`; repetições sem abrir o browser |
| [007](ADR-007-empacotamento-com-docker.md) | Empacotamento com Docker | Imagem oficial do Playwright; alvos `dev` e `prod`; `data/` em bind mount |
| [008](ADR-008-catalogo-pela-rede-da-pagina.md) | Catálogo pela rede da página | O robô navega e escuta o JSON que a própria página pede; nenhum endpoint no código |
| [009](ADR-009-waha-para-demonstracao.md) | WAHA para a demonstração | Envio real pelo WAHA (não oficial, só para demo); Cloud API da Meta documentada como caminho para produção |
| [010](ADR-010-reenvio-com-dados-reaproveitados.md) | Reenvio com dados reaproveitados | Cada clique envia; a consulta já feita não é coletada de novo; o banco só barra duplicata em andamento |

Todos os ADRs acima estão com status **Aceito**, exceto o 003, substituído pelo 009.

## Formato

Cada documento segue a mesma estrutura:

```
# ADR-NNN — Título
**Status:** Proposto | Aceito | Substituído por ADR-NNN · data

## Contexto        o que motivou a decisão; fatos observados, não opiniões
## Decisão         o que foi decidido, no presente do indicativo
## Justificativa   por que esta e não outra
## Consequências   o que ganhamos e o que passamos a conviver
## Alternativas consideradas   o que foi descartado e por quê
```

A seção de consequências registra também as **negativas**. Um ADR que só lista benefícios não está documentando uma decisão — está vendendo uma.

## Status

| Status | Significado |
|---|---|
| **Proposto** | em discussão, ainda não vale |
| **Aceito** | em vigor |
| **Substituído por ADR-NNN** | não vale mais; o documento permanece no repositório |

ADRs **não são editados** depois de aceitos, exceto para correção factual. Quando uma decisão muda, cria-se um ADR novo que substitui o anterior, e o antigo é marcado — o histórico do raciocínio é justamente o que dá valor ao registro.

## Como adicionar um ADR

1. Numere na sequência: `ADR-006-titulo-em-kebab-case.md`
2. Siga o formato acima, com status **Proposto**
3. Acrescente a linha no índice deste arquivo
4. Ao aceitar, mude o status e a data

## Relacionado

- [`docs/DECISOES-TECNICAS.md`](../DECISOES-TECNICAS.md) — registro corrente de decisões técnicas, de granularidade mais fina que os ADRs, incluindo escolhas pequenas de implementação e comparações conceituais
- [`docs/PRD.md`](../PRD.md) — o produto e seus requisitos
- [`CLAUDE.md`](../../CLAUDE.md) — padrões de código e armadilhas da fonte de dados
