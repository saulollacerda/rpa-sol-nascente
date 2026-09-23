# PRD — Radar de Consórcio de Motos

**Produto:** painel interno que coleta dados públicos do Banco Central sobre o mercado de consórcio de motocicletas e entrega um relatório de inteligência comercial no WhatsApp.

**Cliente:** Sol Nascente Motos — concessionária Honda, praças **Piauí e Maranhão**.

**Status:** MVP / desafio técnico
**Última atualização:** 2026-09-22

---

## 1. Problema

A Sol Nascente Motos vende consórcio Honda, mas opera às cegas quanto ao mercado em que está inserida. Não sabe responder perguntas básicas do dia a dia comercial:

- Quantas pessoas aderiram a consórcio de moto no Piauí e no Maranhão neste trimestre?
- Quantas foram **contempladas** — ou seja, quantos consumidores estão com carta de crédito na mão, prontos para comprar uma moto?
- A Honda está ganhando ou perdendo espaço para BB, Yamaha e Sperta na nossa praça?

O Banco Central publica exatamente esses dados, por administradora, segmento e unidade da federação. O problema é o acesso: a informação está em arquivos ZIP de CSV mal formatados, atrás de um formulário ASP legado, embutido dentro de uma aplicação Angular. Não existe relatório pronto nem API para esse recorte. Na prática, ninguém na concessionária vai buscar esse dado manualmente todo trimestre.

## 2. Usuário e job-to-be-done

**Usuário:** gestor comercial da concessionária (perfil administrativo, não técnico).

> *"Quando começa um novo trimestre, quero receber no WhatsApp um retrato de quantas pessoas entraram e foram contempladas em consórcio de moto nas minhas praças, para eu direcionar a equipe de vendas e saber se a Honda está mantendo a liderança."*

O usuário não quer explorar dados. Quer **escolher os parâmetros uma vez e receber um relatório pronto para ler no celular** — e ter o histórico do que já foi consultado e enviado.

## 3. Fonte de dados

Banco de dados de consórcios do Banco Central do Brasil:
`https://www.bcb.gov.br/estabilidadefinanceira/consorciobd`

Dois conjuntos são utilizados, porque as métricas relevantes estão divididas entre eles:

| Conjunto | Granularidade | Periodicidade | Mais recente | Aporta |
|---|---|---|---|---|
| Dados consolidados | administradora × segmento | mensal | Julho/2026 | taxa de administração, grupos ativos, cotas ativas e excluídas, inadimplência |
| Dados por UF | administradora × segmento × UF | trimestral | Junho/2026 | recorte geográfico, contemplados por lance vs sorteio, adesões no trimestre |

Como as periodicidades diferem, o relatório informa a data-base de cada bloco em vez de assumir uma só.

O segmento de interesse é o **4 — "motocicletas e motonetas"**, conforme o dicionário de campos do próprio BCB.

> Detalhes técnicos da coleta e do tratamento estão em [ADR-002](adr/ADR-002-fonte-bcb-e-estrategia-de-rpa.md).

## 4. Escopo do MVP

```
Painel de parâmetros → Executar RPA → Visualizar relatório → Enviar WhatsApp → Histórico
```

1. O usuário monta a consulta no painel administrativo.
2. O sistema executa o RPA: navega no site do BCB, seleciona a data-base, baixa os arquivos.
3. Os CSVs são normalizados e filtrados conforme os parâmetros.
4. Um relatório em texto é gerado dinamicamente a partir dos números apurados.
5. O relatório é enviado para um número de WhatsApp.
6. Toda a execução fica registrada e consultável.

## 5. Painel de parâmetros

Todos os filtros derivam de colunas que existem de fato nos CSV do BCB — o painel não inventa dimensão que a fonte não tem.

| Parâmetro | Tipo | Default | Origem |
|---|---|---|---|
| Data-base | seleção única | mais recente disponível | as próprias opções do formulário do BCB |
| Segmento | seleção única (1–6) | **4 — motocicletas e motonetas** | `Código_do_segmento` |
| UF | **múltipla** (27) | **PI, MA** | `Unidade_da_Federação_do_consorciado` |
| Administradora | busca por nome ou CNPJ, múltipla | Consórcio Nacional Honda | `Nome_da_Administradora` / `CNPJ_da_Administradora` |
| Métricas | múltipla | adesões, contemplados (lance e sorteio), ativos, share | colunas numéricas dos dois CSV |
| Comparar concorrentes | liga/desliga + N | ligado, top 5 | derivado |
| Destinatário | telefone E.164 | valor do `.env` | — |

As opções de data-base **não são hardcoded**: são lidas do formulário do BCB na própria execução, então o painel acompanha automaticamente as publicações novas.

## 6. Relatório gerado

Exemplo real, com os números apurados da fonte (consolidado Julho/2026, UF Junho/2026):

```
📊 RADAR DE CONSÓRCIO DE MOTOS
Segmento 4 (motocicletas e motonetas)
Praças: data-base Junho/2026 · Nacional: Julho/2026

🏍️ SUAS PRAÇAS

PIAUÍ — 155.648 consorciados ativos · 40 administradoras
  Consórcio Nacional Honda
    Ativos ............... 148.962  (95,7% da praça)
    Adesões no trimestre .. 19.340
    Contemplados .......... 10.305  (9.354 lance · 951 sorteio)
  Concorrência: BB 1,8% · Yamaha 0,9% · Âncora 0,5%

MARANHÃO — 249.533 consorciados ativos · 45 administradoras
  Consórcio Nacional Honda
    Ativos ............... 228.238  (91,5% da praça)
    Adesões no trimestre .. 27.261
    Contemplados .......... 13.402  (12.032 lance · 1.370 sorteio)
  Concorrência: Yamaha 3,3% · BB 1,9% · Suzuki Motos 0,7%

🎯 OPORTUNIDADE
23.707 consumidores contemplados nas duas praças neste trimestre
— carta de crédito disponível para aquisição de moto.

🇧🇷 CONTEXTO NACIONAL
Honda lidera com 77,3% do mercado (2,57 mi de 3,32 mi de cotas ativas)
Taxa de administração: 23,2% · 3.760 grupos ativos
Seguidos por BB 4,4% · Yamaha 3,9% · Itaú 1,9%

Fonte: Banco Central do Brasil · gerado em 22/09/2026 15:12
```
O formato é texto puro com emojis, otimizado para leitura no WhatsApp — sem tabelas, que quebram no app.

## 7. Regras de negócio

- **Share da praça** = ativos da administradora ÷ soma dos ativos de todas as administradoras naquela UF e segmento. Calculado sobre o dataset completo antes de aplicar o filtro de administradora, senão o percentual sairia sempre 100%.
- **Consorciados ativos** = contemplados por lance + contemplados por sorteio + não contemplados.
- **Multi-UF** não soma praças num número único: cada UF é apresentada como bloco próprio, porque a decisão comercial é por praça. O total consolidado aparece apenas no bloco de oportunidade.
- **Consulta sem resultado** é um desfecho legítimo, não um erro: se a administradora não opera na UF e segmento escolhidos, a execução termina em `SEM_RESULTADO`, registra o motivo e **não dispara envio**.
- **Divergência de periodicidade**: o consolidado é mensal e o de UF é trimestral. As praças usam **o trimestre mais recente até a data-base escolhida** — para Julho/2026, Junho/2026 — e o relatório informa a data-base de cada bloco. Só quando não há trimestre publicado até a data (antes de 2008) o relatório sai apenas com o bloco nacional, avisando a ausência do recorte geográfico.

  > **Revisão (2026-09-22):** a regra original emitia só o bloco nacional sempre que a data-base não tivesse arquivo de UF. Como o arquivo de UF é trimestral, isso deixaria oito de cada doze meses sem as praças, que são o principal interesse do gestor.

## 8. Requisitos não-funcionais

Mapeados contra a lista de *"Requisitos importantes"* do enunciado:

| Exigência do desafio | Como é atendida | Onde |
|---|---|---|
| Código organizado, separação de responsabilidades | camadas `api / domain / rpa / parsing / infra`, domínio sem dependência de I/O | [ADR-001](adr/ADR-001-stack-e-arquitetura.md) |
| Tratamento de erros e logs | exceções de domínio próprias, logging estruturado com `execucao_id` | [ADR-001](adr/ADR-001-stack-e-arquitetura.md), [ADR-004](adr/ADR-004-persistencia-e-idempotencia.md) |
| Armazenamento do histórico | tabela `execucoes` com parâmetros, resultado, mensagem e status | [ADR-004](adr/ADR-004-persistencia-e-idempotencia.md) |
| Evitar processamento/envio duplicado | `parametros_hash` SHA-256 com unique constraint + cache de artefatos | [ADR-004](adr/ADR-004-persistencia-e-idempotencia.md) |
| Credenciais fora do código | `pydantic-settings` + `.env` versionado apenas como `.env.example` | [ADR-005](adr/ADR-005-configuracao-e-segredos.md) |
| README com instruções | instalação, configuração, uso, testes e solução de problemas | [README](../README.md) |

Cenários de falha que a solução precisa cobrir, conforme o enunciado: consulta sem resultado, informações incompletas, indisponibilidade temporária da fonte, falha durante a navegação e tentativa de processamento duplicado.

## 9. Fora de escopo

- Autenticação e multiusuário — é uma ferramenta interna de uso único.
- Agendamento automático (execução recorrente por cron) — o disparo é manual pelo painel.
- Série histórica e gráficos de evolução — o relatório é um retrato de uma data-base.
- Segmentos além do 4 em profundidade — os outros são selecionáveis, mas o produto é pensado para motos.
- Envio para múltiplos destinatários ou listas de transmissão.
