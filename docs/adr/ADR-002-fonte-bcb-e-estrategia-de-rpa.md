# ADR-002 — Fonte BCB e estratégia de RPA

**Status:** Aceito · 2026-09-22

## Contexto

A fonte é o banco de dados de consórcios do Banco Central, em
`https://www.bcb.gov.br/estabilidadefinanceira/consorciobd`.

Investigar essa página revelou quatro fatos que definiram a estratégia — e um deles quase nos levou a construir sobre dado errado.

### 1. A URL oficial não devolve dados

É uma aplicação Angular. O HTML inicial tem **2.871 bytes** e nenhum número: o conteúdo é montado por JavaScript. Um `curl` na URL divulgada retorna casca vazia.

### 2. Existe um espelho legado, e ele está defasado

A busca por uma via sem JavaScript leva à página ASP antiga,
`fis/consorcios/port/consorcio_banco_de_dados.asp?idpai=consorcio&frame=1`,
que renderiza três formulários com `<select name="PARAMETRO">` nativos e responde a `curl`. É uma armadilha.

| | ASP legado | Página Angular atual |
|---|---|---|
| Componente | `<select>` / `<option>` nativos | `ng-select` (`<div class="ng-option">`) |
| Rótulo da opção | `Julho/2026 (105 KB)` | `202607Consorcios (106.3 Kb)` |
| Consolidado mais recente | Maio/2026 | **Julho/2026** |
| Por UF mais recente | Março/2026 | **Junho/2026** |
| Caminho dos arquivos | `/Fis/Consorcios/Port/BD/` | `/content/estabilidadefinanceira/consorcio-banco-de-dados/` |

São **duas fontes distintas**, não duas visões da mesma. O ASP está cerca de dois meses atrasado e serve arquivos de outro diretório. Automatizar contra ele entregaria dado velho silenciosamente, sem erro nenhum — o pior tipo de falha.

Confirmado que a defasagem não é cache: um fetch com `Cache-Control: no-cache` retornou `x-cache: TCP_MISS` e ainda assim listava Maio/2026.

### 3. Caminho real dos arquivos

```
/content/estabilidadefinanceira/consorcio-banco-de-dados/
    dados-consolidados/AAAAMMConsorcios.zip
    dados-por-unidade-da-federacao/AAAAMMConsorcios_UF.zip
    dados-contabeis-descontinuados/        → descontinuado, não usado
```

> **Correção factual (2026-09-22):** esta seção listava a terceira pasta como `dados-por-administradora/`. O spike contra o site real mostrou que ela se chama **"Dados contábeis consolidados (descontinuado)"**, fica em `/dados-contabeis-descontinuados` e contém arquivos `ConsorciosAdministradoras_*.zip`. O nome `_ADM` é do formulário ASP legado. Ver [ADR-008](ADR-008-catalogo-pela-rede-da-pagina.md).

### 4. Conteúdo dos arquivos

- `AAAAMMConsorcios.zip` → `Segmentos_Consolidados.csv`, 750 linhas, chave `administradora × segmento`. Traz taxa de administração, grupos ativos, cotas ativas e excluídas, inadimplência. **Mensal.**
- `AAAAMMConsorcios_UF.zip` → `Consorcios_UF.csv`, 7.667 linhas, chave `administradora × segmento × UF`, com `Significado_dos_campos_UF.csv`. Traz contemplados por lance vs sorteio, não contemplados e adesões. **Trimestral.**

Não existe relatório pronto nem API pública para o recorte `administradora × segmento × UF` de que o produto precisa.

## Decisão

**Usar Playwright com browser real**, contra a página Angular — nunca contra o ASP legado.

Os dois conjuntos são baixados para a data-base escolhida, com parsers distintos atrás de uma interface comum, porque as métricas relevantes estão divididas: taxa de administração e inadimplência só existem no consolidado; UF, adesões e contemplação por lance vs sorteio só existem no de UF.

As data-bases disponíveis são **lidas do `ng-select` em tempo de execução**, nunca hardcoded.

## Justificativa

O argumento é direto e não depende de preferência: **o dropdown é um `ng-select`, não um `<form>` nativo.** Não há formulário para submeter nem `<option value>` para ler sem executar JavaScript. Um cliente HTTP não tem como interagir com esse componente. Browser real não é a opção mais elegante — é a única que funciona contra a fonte correta.

Vale registrar a tentação que rejeitamos: conhecendo o padrão de nome, dava para montar a URL do ZIP e baixar por HTTP direto, muito mais rápido. Descartamos porque equivale a hardcodar a URL de download — se o BCB mudar o esquema de diretórios, como acabou de fazer ao migrar do ASP para o CMS, a automação quebra em silêncio ou, pior, continua baixando de um caminho antigo que ainda responde. Ler as opções que a página oferece é o que sobrevive a esse tipo de migração.

Some-se a isso que *"estratégia de navegação e extração dos dados"* é critério explícito de avaliação do desafio.

## Tratamento dos dados

Cada item abaixo foi observado nos arquivos reais, não presumido:

| Característica | Tratamento |
|---|---|
| Encoding `windows-1252` | leitura explícita com `cp1252`; ler como UTF-8 quebra em "CONSÓRCIO" |
| Separador `;` | declarado no parser |
| Decimal com vírgula (`23,2`) | conversão para `float` com troca de separador |
| `Nome_da_Administradora` com padding de espaços | `strip()` obrigatório, senão o agrupamento por nome duplica registros |
| CNPJ com apenas a raiz de 8 dígitos, zero-padded (`00000776`) | tratado como string; converter para inteiro perde os zeros à esquerda |
| Dicionário declara `Data_base` como `AAAA-MM`, arquivo traz `202606` | confiar no arquivo, não na documentação |
| Cabeçalho começa com `#` (`#Nome_da_Administradora`) | primeira coluna precisa ser renomeada |
| Consolidado mensal, UF trimestral | data-bases não coincidem; o relatório informa a data-base de cada bloco |

## Cenários de falha

| Cenário | Comportamento |
|---|---|
| Site fora do ar ou lento | timeout do Playwright → `FALHA_COLETA`, com a mensagem registrada |
| Data-base sem arquivo de UF (mês não trimestral) | relatório emitido só com o bloco nacional, avisando a ausência do recorte |
| Layout ou componente mudou | seletor não encontrado → `ColetaError` com o seletor esperado no log |
| ZIP corrompido ou vazio | `ParsingError`, sem mascarar o problema com dado parcial |
| Administradora não opera na UF/segmento | desfecho `SEM_RESULTADO`, **sem envio de WhatsApp** |
| Dado servido mais antigo que o esperado | a data-base efetivamente coletada é registrada na execução e exibida no relatório |

O último item existe por causa da armadilha do ASP: o sistema nunca afirma qual data-base tem — ele **reporta a que coletou**.

## Consequências

**Positivas** — a coleta reflete o que um humano veria na fonte oficial e atual; resiliência a mudanças de diretório e de nomenclatura; a camada de parsing fica isolada e testável com um ZIP fixado, sem rede.

**Negativas** — Playwright é dependência pesada, baixa binários de browser, e a coleta leva dezenas de segundos em vez de milissegundos. O custo de tempo é mitigado pelo cache de artefatos descrito em [ADR-004](ADR-004-persistencia-e-idempotencia.md).

## Alternativas consideradas

**Automatizar o ASP legado.** Seria mais simples: `<select>` nativo, `POST` para `download.asp`, sem JavaScript. **Rejeitada por servir dado defasado em ~2 meses.** Fica registrado aqui para que ninguém "simplifique" a solução nessa direção depois.

**Montar a URL do ZIP e baixar por HTTP.** Rápido e sem browser, agora que o padrão de caminho é conhecido. Rejeitada por fragilidade a mudança de diretório — mas o parser é independente da coleta, então trocar a estratégia depois custaria pouco.

**Portal de Dados Abertos / API Olinda do BCB.** Há API para filiais de administradoras e séries agregadas do SGS, mas nenhuma expõe o recorte `administradora × segmento × UF`. Não atende ao requisito.

**Série histórica com todas as data-bases.** Fora do escopo do MVP, que é o retrato de uma data-base.
