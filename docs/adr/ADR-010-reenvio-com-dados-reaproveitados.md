# ADR-010 — Reenvio com dados reaproveitados

**Status:** Aceito · 2026-09-23 · substitui a regra de reenvio do [ADR-004](ADR-004-persistencia-e-idempotencia.md)

## Contexto

O ADR-004 tratava uma consulta já enviada como concluída para sempre. O `parametros_hash` tinha *unique constraint*, então cada combinação de parâmetros tinha uma única linha. Pedir de novo devolvia `REUSAR`, e nada era enviado.

Na prática, isso contraria o uso. Quando o gestor clica em **Gerar e enviar relatório**, ele quer o relatório no WhatsApp: para mandar de novo a si mesmo, para reencaminhar numa conversa, ou porque apagou a mensagem. Receber "já foi enviado" parece defeito.

O que o ADR-004 queria evitar continua valendo, mas são duas coisas diferentes:

- **Reprocessar** é caro: abrir o site do BCB, baixar os ZIPs, cruzar os datasets.
- **Enviar em duplicidade por acidente** é ruído: clique duplo, ou dois pedidos iguais em sequência.

O reenvio **pedido** não é nenhuma das duas.

## Decisão

**Cada clique envia. A coleta é que não se repete.** O serviço decide olhando a execução **mais recente** com a mesma chave:

| Mais recente | Decisão | O que acontece |
|---|---|---|
| nenhuma | `CRIAR` | coleta, processa e envia |
| `ENVIADO` | **`REENVIAR`** | **nova execução** que herda `dados_encontrados` e `mensagem_gerada` da anterior e vai direto ao envio |
| em andamento | `REUSAR` | devolve a execução em curso: o clique duplo não duplica |
| `FALHA_*` | `RETENTAR` | reabre a mesma linha; numa `FALHA_ENVIO`, só reenvia a mensagem já gerada |
| `SEM_RESULTADO` | `REUSAR` | não há relatório para enviar |

A execução reenviada passa de `PENDENTE` direto a `MENSAGEM_GERADA`, uma transição nova e exclusiva do reaproveitamento. Depois segue `ENVIANDO → ENVIADO` como qualquer outra. A coluna `origem_id` aponta para a execução de onde vieram os dados, e o painel mostra "Dados reaproveitados da execução #N".

**A unicidade continua no banco, agora parcial.** A *unique constraint* em `parametros_hash` foi trocada por um índice único parcial, que vale só enquanto a execução está em andamento:

```sql
CREATE UNIQUE INDEX uq_execucoes_chave_em_andamento ON execucoes (parametros_hash)
WHERE status IN ('PENDENTE', 'COLETANDO', 'PROCESSANDO', 'MENSAGEM_GERADA', 'ENVIANDO');
```

Duas execuções da mesma consulta em curso ao mesmo tempo continuam impossíveis, e é o banco que garante isso. Execuções concluídas da mesma chave podem se acumular: cada uma é um envio no histórico.

Bancos criados antes desta decisão são migrados na subida da API (`criar_tabelas`): a unique antiga sai, o índice parcial entra e a coluna `origem_id` é criada. A migração é idempotente.

## Justificativa

Separar "não reprocessar" de "não reenviar" atende o usuário sem abrir mão do controle que o desafio pede. O processamento duplicado continua evitado, porque o reenvio não abre o navegador. O envio duplicado **acidental** também, porque o índice parcial barra pedidos simultâneos.

Uma linha por envio, em vez de reenviar reabrindo a mesma linha, mantém a rastreabilidade: cada envio tem o seu `enviado_em` e o seu `provider_message_id`. Reabrir a linha sobrescreveria o registro do envio anterior.

## Consequências

**Positivas:**
- O botão faz o que diz.
- O reenvio leva segundos, sem abrir o site do BCB.
- Uma falha de envio agora é retentada sem coletar de novo.

**Negativas:**
- **O reenvio usa os números da consulta original.** O BCB revisa as últimas 12 data-bases (ver [ADR-006](ADR-006-estrategia-de-cache-e-revalidacao.md)), então um reenvio semanas depois pode carregar um número já revisado. Para forçar dado novo, hoje é preciso mudar algum parâmetro.
- O mesmo relatório pode ser enviado várias vezes, **de propósito**. O controle agora é contra o acidente, não contra a intenção.

## Alternativas consideradas

- **Reenviar reabrindo a mesma linha (`ENVIADO → ENVIANDO`):** mais simples, mas perde o registro de cada envio anterior.
- **Coletar de novo a cada clique:** sempre usaria dado fresco, mas repete o processamento que o desafio pede para evitar, e deixa o reenvio lento.
- **Botão separado "Reenviar" no histórico:** deixaria a intenção explícita, mas adiciona uma interação que o gestor não pediu. Ele espera que o botão principal envie.
