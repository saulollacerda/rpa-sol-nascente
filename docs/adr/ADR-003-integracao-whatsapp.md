# ADR-003 — Integração com WhatsApp

**Status:** Aceito · 2026-09-22

## Contexto

O relatório precisa chegar a um número de WhatsApp. O enunciado pede explicitamente que a estratégia de integração seja **definida e justificada tecnicamente**, o que torna esta decisão um item de avaliação por si só.

O WhatsApp não tem uma via de integração única. As opções se dividem entre o canal oficial da Meta, intermediários comerciais e bibliotecas não oficiais que automatizam o WhatsApp Web. As diferenças entre elas são de legalidade e de sustentabilidade, não apenas de conveniência.

Há ainda uma restrição de contexto: a solução será apresentada ao vivo. Uma integração que dependa de token válido, número de teste ativo e conectividade no momento da apresentação é um risco concreto.

## Decisão

Definir uma interface `WhatsAppSender` no domínio e fornecer **duas implementações**, selecionadas em tempo de execução pela variável `WHATSAPP_PROVIDER`:

```python
class WhatsAppSender(Protocol):
    def enviar(self, destinatario: str, mensagem: str) -> ResultadoEnvio: ...
```

- **`CloudApiSender`** — WhatsApp Business Cloud API da Meta, via Graph API. Usa o número de teste gratuito, envia template message e recebe status de entrega por webhook.
- **`FakeSender`** — registra a mensagem em log e persiste a execução exatamente como o adapter real, sem tocar a rede.

O domínio depende apenas do `Protocol`. Nenhuma camada de negócio sabe qual adapter está ativo.

## Justificativa

A **Cloud API é a via oficial e suportada**. É o caminho que uma concessionária realmente seguiria para colocar isso em produção: número comercial verificado, templates aprovados, status de entrega auditável e conformidade com os termos da Meta. Escolher a via oficial é a decisão defensável quando a pergunta é "como isso viraria um sistema de produção?" — que é exatamente o que o enunciado pede na apresentação final.

O **`FakeSender` não é um atalho, é desenho**. Ele resolve três problemas de uma vez: permite testar o fluxo completo sem consumir cota nem depender de rede; garante que a demonstração ao vivo não quebre por token expirado ou rate limit; e força a fronteira de abstração a ser real, porque duas implementações concretas provam que o domínio não vazou detalhe de infraestrutura.

O envio é a última etapa da execução e **nunca dispara** quando o desfecho é `SEM_RESULTADO` ou quando houve falha de coleta ou parsing — não faz sentido notificar sobre um relatório que não existe.

## Consequências

**Positivas** — o domínio fica testável sem rede; a apresentação não depende de infraestrutura externa; trocar de provedor depois é implementar uma classe.

**Negativas** — a Cloud API exige criar um app no Meta Business Manager e aprovar template, o que é burocrático e tem prazo. O número de teste gratuito da Meta só envia para destinatários previamente cadastrados, limitação aceitável para demonstração mas que precisa ser explicada. Manter dois adapters significa manter dois caminhos de código.

**Risco assumido** — se a aprovação do template não sair a tempo, a demonstração roda com `FakeSender` e a integração real é mostrada por código e configuração. A decisão arquitetural permanece válida e defensável.

## Alternativas consideradas

**Twilio (WhatsApp Sandbox).** Configuração em minutos, SDK trivial, sandbox público sem burocracia de aprovação. Descartada porque introduz um intermediário pago no caminho e enfraquece o argumento central: a pergunta "como isso vira produção?" se responde melhor apontando para o canal oficial do que para um revendedor.

**whatsapp-web.js / Baileys.** Automatizam a sessão do WhatsApp Web via QR code. Custo zero e demonstração imediata. Descartadas por **violarem os termos de uso da Meta** — o número usado pode ser banido — e por serem estruturalmente frágeis, já que dependem de engenharia reversa de um protocolo não documentado e quebram a cada mudança do WhatsApp Web. Recomendar isso a um cliente real seria irresponsável.

**Link `wa.me` com mensagem pré-preenchida.** Não é envio automatizado: exige que um humano aperte "enviar". Não atende ao requisito.
