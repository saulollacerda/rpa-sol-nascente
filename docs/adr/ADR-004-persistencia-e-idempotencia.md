# ADR-004 — Persistência e idempotência

**Status:** Aceito · 2026-09-22 · regra de reenvio substituída pelo [ADR-010](ADR-010-reenvio-com-dados-reaproveitados.md) em 2026-09-23

> Uma consulta já enviada agora é **reenviada** a cada pedido, reaproveitando os dados sem nova coleta. A *unique constraint* em `parametros_hash` virou um índice único parcial, que vale só para as execuções em andamento. O restante deste ADR (SQLite, hash canônico, máquina de estados e campos registrados) segue valendo.

## Contexto

O enunciado exige registrar consulta realizada, informações encontradas, data e hora, destinatário, mensagem gerada, status do processamento e do envio, e a descrição do erro quando houver. Exige também **controle para evitar processamento ou envio duplicado**.

Duplicidade aqui tem duas faces com custos diferentes. Reprocessar é caro em tempo — cada execução baixa dezenas de megabytes do BCB e leva dezenas de segundos. Reenviar é caro em reputação: mandar o mesmo relatório duas vezes para o gestor comercial é ruído, e no WhatsApp ainda consome cota de mensagens.

## Decisão

**SQLite via SQLAlchemy**, arquivo local. Uma tabela `execucoes` concentra todo o ciclo de vida.

### Chave de idempotência

Cada execução carrega um `parametros_hash`: SHA-256 sobre a tupla canônica dos parâmetros da consulta.

```
sha256( data_base | segmento | ufs_ordenadas | administradoras_ordenadas
        | metricas_ordenadas | destinatario )
```

A ordenação das coleções é obrigatória: selecionar `[PI, MA]` e `[MA, PI]` é a mesma consulta e precisa produzir o mesmo hash. A coluna tem **unique constraint** — é o banco, e não a aplicação, que garante a regra.

Ao receber uma consulta cujo hash já existe com status `ENVIADO`, o sistema não reexecuta: retorna a execução anterior e informa ao usuário que aquele relatório já foi enviado, oferecendo forçar uma nova execução de forma explícita.

### Máquina de estados

```
PENDENTE → COLETANDO → PROCESSANDO → MENSAGEM_GERADA → ENVIANDO → ENVIADO
                │            │               │              │
                ▼            ▼               ▼              ▼
          FALHA_COLETA  FALHA_PROCESSAMENTO  │         FALHA_ENVIO
                             SEM_RESULTADO ──┘
```

`SEM_RESULTADO` é desfecho de sucesso, não falha: a consulta rodou e a resposta é que não há dado para aqueles parâmetros. Não dispara envio.

Os estados intermediários (`COLETANDO`, `PROCESSANDO`, `ENVIANDO`) existem para que o frontend mostre progresso real e para que execuções órfãs — interrompidas por queda do processo — sejam identificáveis.

### Campos registrados

`id` · `parametros_hash` · `parametros` (JSON) · `status` · `criado_em` · `atualizado_em` · `dados_encontrados` (JSON com os números apurados) · `mensagem_gerada` · `destinatario` · `enviado_em` · `provider_message_id` · `erro_tipo` · `erro_descricao`.

Guardar `dados_encontrados` separado de `mensagem_gerada` permite reemitir a mensagem com outro formato sem repetir a coleta, e deixa o histórico auditável: dá para conferir o número que originou cada texto enviado.

### Cache de artefatos

Os ZIPs baixados são guardados em `data/` nomeados pela data-base, para que uma execução não rebaixe um arquivo que já tem.

> **Correção factual (2026-09-22):** esta seção previa cache permanente por data-base. Medições posteriores mostraram que o gargalo é a navegação, não o download, e que o BCB revisa os arquivos das últimas 12 data-bases — o que tornaria o cache permanente uma fonte de dado desatualizado. A estratégia completa, em três camadas e com revalidação por `ETag`, está no [ADR-006](ADR-006-estrategia-de-cache-e-revalidacao.md).

## Justificativa

SQLite é a escolha certa para a escala real do produto: um usuário, execuções manuais, dezenas de registros. Não exige serviço para subir na apresentação, o banco inteiro é um arquivo, e via SQLAlchemy a migração para PostgreSQL seria trocar a connection string.

O hash determinístico é preferível a comparar os parâmetros campo a campo porque reduz a regra a uma única constraint no banco — impossível de contornar por esquecimento em algum caminho de código. Incluir o destinatário na chave é intencional: o mesmo relatório para outra pessoa é um envio legítimo, não duplicata.

O cache de artefatos serve a três propósitos ao mesmo tempo: torna a demonstração rápida na segunda execução, reduz carga sobre um serviço público, e é a segunda camada de defesa contra reprocessamento. Sua política de invalidação está detalhada no [ADR-006](ADR-006-estrategia-de-cache-e-revalidacao.md).

## Consequências

**Positivas** — anti-duplicidade garantida pelo banco; histórico completo e auditável; demonstração rápida após o primeiro download.

**Negativas** — SQLite não suporta escrita concorrente de verdade, irrelevante neste uso mas limitante se o produto crescesse. O diretório `data/` cresce indefinidamente; o MVP não implementa expurgo. Execuções interrompidas ficam presas em estado intermediário — a máquina de estados permite detectá-las, mas a retomada automática está fora do escopo.

## Alternativas consideradas

**PostgreSQL.** Correto para produção, mas exigiria Docker ou serviço local na apresentação, sem benefício nesta escala.

**Arquivos JSON no disco.** Simples demais: não dá constraint de unicidade, e a garantia anti-duplicidade voltaria a depender de disciplina no código.

**Idempotência só em memória durante a sessão.** Não sobrevive a reinício do processo, que é exatamente quando o reenvio acidental acontece.
