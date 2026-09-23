# ADR-008 — Catálogo lido da resposta de rede da própria página

**Status:** Aceito · 2026-09-22

## Contexto

O [ADR-006](ADR-006-estrategia-de-cache-e-revalidacao.md) define um catálogo com as data-bases disponíveis e **a URL de cada arquivo**, e previa lê-lo do `ng-select`. Um spike contra o site real mostrou que isso não fecha: o rótulo da opção traz só nome e tamanho (`202606Consorcios_UF (103.4 Kb)`), e a URL só aparece depois de clicar em "Baixar arquivo".

O mesmo spike revelou de onde a página tira a lista. Ao carregar, o Angular faz três requisições a uma API interna do BCB:

```
/api/servico/sitebcb/Documentos/byListGuid
    ?tronco=estabilidadefinanceira
    &guidLista=96d9c6b3-039e-485e-a8cd-f755367937e0
    &ordem=DataDocumento desc
    &pasta=/dados-consolidados            (355 itens)
          /dados-por-unidade-da-federacao (72 itens)
          /dados-contabeis-descontinuados (98 itens)
```

A resposta vem como `{"conteudo": [...]}`, e cada item traz o que o catálogo precisa:

```json
{"Url": "/content/estabilidadefinanceira/consorcio-banco-de-dados/dados-por-unidade-da-federacao/202606Consorcios_UF.zip",
 "Nome": "202606Consorcios_UF.zip",
 "Tamanho": "105859",
 "DataPublicacao": "2026-08-28T13:19:00Z",
 "DataDocumento": "2026-06-01T03:00:00Z"}
```

### O que o spike verificou

| Etapa | Resultado |
|---|---|
| Carregar a página | 8,1s, sem proteção contra robô |
| Banner de cookies | sobrepõe o conteúdo; some com "Rejeitar cookies" |
| Localizar as seções | títulos `<h4>`, encontrados pelo texto exato |
| Botão "Baixar arquivo" | desabilitado até escolher uma opção |
| Opções | 355 e 72, todas renderizadas, sem virtual scroll |
| Download | evento real de download do navegador, 2,3s |
| Integridade | SHA-256 idêntico ao da fixture obtida por outro caminho |

## Decisão

O robô **navega a página normalmente e escuta as respostas de rede que ela mesma faz**. O catálogo é montado a partir desse JSON, e não do texto das opções.

Cada item é classificado pelo **padrão do nome do arquivo**, não pelo endereço da API nem pela pasta:

| Dataset | Padrão de `Nome` |
|---|---|
| Consolidado | `AAAAMMConsorcios.zip` |
| Por UF | `AAAAMMConsorcios_UF.zip` |
| Qualquer outro | ignorado |

O download continua sendo feito pelo navegador: escolher a opção no `ng-select` e clicar em "Baixar arquivo".

## Justificativa

A decisão preserva o princípio do [ADR-002](ADR-002-fonte-bcb-e-estrategia-de-rpa.md): **o navegador segue sendo a única fonte**. Nenhum endereço de API, `guidLista` ou pasta fica escrito no código — o robô lê o que a página pediu, seja qual for. Se o BCB trocar o endpoint, o `guid` ou a organização de pastas, e a página continuar funcionando para um humano, o robô continua funcionando também.

E ganha-se o que o texto do dropdown não dava: a URL de cada arquivo, a data de publicação e o tamanho em bytes, já estruturados, sem extrair nada de rótulo de interface.

Classificar pelo nome do arquivo em vez da pasta é deliberado. O nome é a dependência que o projeto já tem — o parser procura `Segmentos_Consolidados.csv` e `Consorcios_UF.csv` dentro dos ZIPs. Não se acrescenta uma dependência nova.

## Consequências

**Positivas** — o catálogo sai completo numa única carga de página, com URL; o cache do ADR-006 passa a ter a informação de que precisa sem baixar nada; `DataPublicacao` permite informar ao gestor quando o dado foi publicado.

**Negativas** — o robô passa a depender de a página carregar a lista por uma requisição JSON. Se o BCB passar a embutir a lista no HTML, a escuta não encontra nada. Nesse caso a coleta falha com `ColetaError` explícito ("catálogo não encontrado"), nunca com catálogo vazio silencioso.

## Alternativas consideradas

**Ler o texto das opções do `ng-select`**, como o ADR-006 previa. Funciona, mas não dá a URL, que só surge depois do download.

**Chamar a API diretamente, sem navegador.** Menos de 1 segundo, contra 8. Rejeitado pelo mesmo motivo que o ADR-002 rejeitou montar a URL do ZIP: exigiria fixar no código um endpoint interno e não documentado, com um `guid` opaco. Uma migração de CMS — como a que já aconteceu uma vez — quebraria a coleta.
