# ADR-006 — Estratégia de cache e revalidação

**Status:** Aceito · 2026-09-22 · implementação parcial: só a camada de catálogo existe; o cache dos ZIPs com `ETag` ainda não foi feito

## Contexto

A pergunta que originou este ADR: se os gestores consultarem repetidamente a data-base mais recente, o sistema baixa os arquivos toda vez?

O [ADR-004](ADR-004-persistencia-e-idempotencia.md) previa guardar os ZIPs em `data/` e reaproveitá-los. Medindo o custo real de uma execução, essa previsão resolve a parte errada do problema:

| Etapa | Custo |
|---|---|
| Playwright: subir o browser, navegar, ler o `ng-select` | **~10–20s** |
| Baixar o ZIP | 1,25s |
| Descompactar e parsear 7.667 linhas | milissegundos |

O download é cerca de 6% do tempo. Cachear só o artefato economizaria 1,25s de uns 20s: o gestor continuaria esperando praticamente o mesmo na segunda consulta.

### O cache permanente também estaria incorreto

A própria página do BCB declara:

> *"A cada data-base são atualizadas as informações relativas aos últimos 12 períodos."*

As administradoras reenviam documentos corrigidos, então o ZIP de uma data-base **muda depois de publicado**. Guardar indefinidamente serviria dado desatualizado sem erro — a mesma classe de falha silenciosa da armadilha do ASP descrita no [ADR-002](ADR-002-fonte-bcb-e-estrategia-de-rpa.md).

### O servidor do BCB suporta revalidação

Verificado contra `202607Consorcios.zip`:

```
ETag: "{8978E92D-F36A-4F96-B4CC-CB5EF2B931C3},13"

If-None-Match      →  HTTP 304, 0 bytes         ✅
If-Modified-Since  →  HTTP 200, 108.814 bytes   ❌ não honrado
```

Revalidar custa **0,56s e zero bytes**, contra 1,25s e 108 KB de um download completo.

**Cuidado com `Last-Modified`:** o arquivo de Set/2024 reporta modificação em agosto de 2026. Não é revisão de conteúdo — é a data da migração do BCB para o CMS novo, que reescreveu todos os arquivos. A data não é evidência de mudança; o `ETag` é.

## Decisão

Cache em três camadas:

| Camada | Conteúdo | Invalidação |
|---|---|---|
| **Catálogo** | data-bases disponíveis e a URL de cada arquivo | TTL de 6 horas |
| **Artefato** | o ZIP em `data/`, com o `ETag` gravado ao lado | `If-None-Match` a cada uso |
| **Parse** | não é cacheado | — |

Fluxo de uma consulta:

```
catálogo fresco? ──não──→ Playwright navega e regrava o catálogo
      │ sim
      ▼
ZIP em data/? ──não──→ baixa, grava ZIP + ETag
      │ sim
      ▼
revalida com If-None-Match
      ├── 304 → usa o arquivo em cache
      └── 200 → substitui o ZIP e o ETag
      ▼
    parse
```

> **Nota (2026-09-22):** a origem do catálogo foi redefinida pelo [ADR-008](ADR-008-catalogo-pela-rede-da-pagina.md). O texto do `ng-select` não traz a URL; o catálogo passou a ser lido da resposta JSON que a própria página requisita.

Resultado: a primeira consulta leva ~20s; as repetições levam menos de 1s **sem abrir o browser**.

O parse não é cacheado porque custa milissegundos — cachear adicionaria estado sem ganho mensurável.

## Justificativa

O ganho está no catálogo, não no artefato. Enquanto a lista de data-bases estiver fresca, o sistema já sabe a URL do arquivo e não precisa navegar para descobri-la. É o que transforma uma operação de 20 segundos numa de menos de um — a diferença entre uma ferramenta que o gestor usa e uma que ele evita.

O TTL de 6 horas vem da natureza da fonte: data-bases novas aparecem uma vez por mês, no dia 10 do segundo mês subsequente. Uma janela de horas é irrelevante para um dado mensal, e ainda assim mantém o sistema honesto sobre publicações novas.

A revalidação por `ETag` resolve o problema oposto: é o que impede que o cache se torne uma fonte de dado velho, respeitando a janela de 12 meses em que o BCB revisa arquivos.

### Sobre a contradição aparente com o ADR-002

Pular o browser parece contrariar a decisão do [ADR-002](ADR-002-fonte-bcb-e-estrategia-de-rpa.md) de não montar a URL do ZIP diretamente. Não é o mesmo caso: **a URL não é inventada a partir de um padrão de nome — ela vem do catálogo que o browser leu da página.** O navegador continua sendo a única fonte de URLs; o cache apenas evita repetir a navegação enquanto o catálogo estiver válido. Expirado o TTL, volta-se a navegar.

Hardcodar o padrão `AAAAMMConsorcios.zip` continua proibido.

## Consequências

**Positivas** — a ferramenta passa a ser utilizável em uso repetido; a carga sobre um serviço público cai bastante; a revalidação impede servir dado revisado desatualizado.

**Negativas** — o TTL do catálogo cria uma janela de até 6 horas em que uma data-base recém-publicada não aparece no painel. Há mais estado para gerenciar: catálogo, artefatos e ETags precisam ser invalidados de forma coerente. O diretório `data/` segue crescendo sem expurgo no MVP.

**Degradação** — se o BCB parar de enviar `ETag`, a revalidação falha para o lado seguro: baixa o arquivo sempre. Fica mais lento, nunca incorreto.

## Alternativas consideradas

**Cache permanente por data-base**, como o ADR-004 previa. Rejeitado: serviria silenciosamente versões desatualizadas dos arquivos que o BCB revisa nos últimos 12 períodos.

**Revalidar por `Last-Modified` / `If-Modified-Since`.** Testado contra o servidor: não é honrado, retorna 200 com o corpo completo. Além disso a data reflete a migração de CMS, não mudança de conteúdo.

**Não cachear nada.** Mais simples e sempre correto, mas impõe ~20s a cada consulta, inclusive nas repetidas.

**Cachear o resultado já parseado.** O parse custa milissegundos; a complexidade não se paga.
