# PRD — Radar de Consórcio de Motos

**Produto:** painel interno que coleta dados públicos do Banco Central sobre o mercado de consórcio de motocicletas e entrega um relatório de inteligência comercial no WhatsApp.

**Cliente:** Sol Nascente Motos — concessionária Honda, praças **Piauí e Maranhão**.

**Status:** MVP / desafio técnico
**Última atualização:** 2026-09-23

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

Exemplo real, enviado pelo sistema para a consulta padrão (data-base Junho/2026, Piauí e Maranhão, Honda e as 3 maiores concorrentes em adesões):

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

O formato é texto com emojis e a formatação nativa do WhatsApp (`*negrito*`, `_itálico_`), otimizado para leitura no celular. Não há tabelas, que quebram no app. As regras de share, concorrentes e alertas estão na [entrada 25 das decisões técnicas](DECISOES-TECNICAS.md#25-regras-do-template-do-relatório).

> **Revisão (2026-09-23):** o exemplo original trazia um bloco por praça com o ranking de concorrentes pela carteira. O relatório passou a seguir o template do analista: recorte somado das UFs, share de carteira comparado ao de adesões, concorrentes escolhidas pelas adesões e alertas de movimento de share e de inadimplência.

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
