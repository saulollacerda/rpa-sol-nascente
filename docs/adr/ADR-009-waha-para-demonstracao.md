# ADR-009 — WAHA para o envio na demonstração

**Status:** Aceito · 2026-09-23 · substitui o [ADR-003](ADR-003-integracao-whatsapp.md) e a parte de WhatsApp do [ADR-005](ADR-005-configuracao-e-segredos.md)

## Contexto

O ADR-003 escolheu a Cloud API da Meta porque ela responde bem à pergunta "como isso vira produção?". Na implementação, o custo apareceu inteiro. Era preciso criar um app no Meta Business, cadastrar cada destinatário na lista de números de teste e respeitar a janela de 24 horas. Uma mensagem de texto só chega a quem escreveu para o número da empresa no último dia; fora disso a Meta devolve o código 131047. Template resolveria a janela, mas os parâmetros de um template não aceitam quebra de linha, e o relatório tem dezenas.

O projeto **não vai para produção**: ele existe para ser demonstrado. Tudo o que a Cloud API exige a mais protege um uso que este projeto não terá, e cada exigência é um jeito de a apresentação ao vivo falhar.

## Decisão

O envio real passa a ser feito pelo **WAHA** (WhatsApp HTTP API, imagem `devlikeapro/waha`, versão Core gratuita). O WAHA conecta um número comum de WhatsApp por QR code e expõe uma API REST. O código não tem mais nenhuma referência à API da Meta.

`WhatsAppSender` continua sendo o `Protocol` do domínio, agora com duas implementações escolhidas por `WHATSAPP_PROVIDER`:

- **`WahaSender`** (`waha`):
  1. Consulta `GET /api/contacts/check-exists` para descobrir o `chatId` real. Números brasileiros antigos existem no WhatsApp **sem o 9º dígito**, e só o WhatsApp sabe qual é o caso.
  2. Envia com `POST /api/sendText`.
  3. Traduz os erros para o que o gestor precisa fazer: WAHA fora do ar, API key inválida, sessão sem QR code escaneado, número sem WhatsApp.
- **`FakeSender`** (`fake`, padrão): sem rede, com o mesmo papel descrito no ADR-003.

O WAHA roda como serviço do `docker-compose.yml` sob o profile `waha`, com a engine `GOWS` (sem Chromium) e a sessão num volume, para o QR code ser escaneado uma vez só.

### Variáveis

| Variável | Segredo | Descrição |
|---|---|---|
| `WHATSAPP_PROVIDER` | não | `fake` (padrão) ou `waha` |
| `WHATSAPP_DESTINATARIO` | dado pessoal | telefone padrão, com DDI e DDD |
| `WAHA_URL` | não | padrão `http://localhost:3000`; no compose, `http://waha:3000` |
| `WAHA_API_KEY` | **sim** | enviada no header `X-Api-Key`; opcional se o WAHA subiu sem key |
| `WAHA_SESSION` | não | padrão `default`, a única sessão da versão Core |

Nenhuma variável é obrigatória: todas têm default ou são opcionais. A validação na inicialização que o ADR-005 previa para o token da Meta deixa de existir. As demais regras do ADR-005 continuam valendo: a key não aparece em log (`X-Api-Key: …` e `api_key=…` são mascarados), nem no `repr` do adapter, nem nas mensagens de erro.

## Justificativa

Para demonstrar, o WAHA remove todos os pontos de falha que a Cloud API trazia. Não há app a aprovar, lista de teste nem janela de 24 horas, e o relatório chega a qualquer número, com as quebras de linha preservadas. O adapter é tão simples quanto o anterior: duas chamadas HTTP, testadas com `httpx.MockTransport`, sem rede.

A abstração se pagou. Trocar de provedor foi reescrever um arquivo de `infra/` e a configuração: domínio, serviço e API ficaram intactos.

## Consequências

**Positivas:** a demonstração envia de verdade com um celular e um QR code. Menos configuração e menos segredos.

**Negativas:**
- **O WAHA não é oficial.** Automatizar o WhatsApp fora da API da Meta viola os termos de uso, e o número conectado pode ser banido. **Use um chip dedicado, nunca o número da concessionária.**
- Depende de engenharia reversa: uma mudança do WhatsApp pode quebrá-lo até sair uma imagem nova.
- A sessão depende do celular. Se o aparelho desconectar o dispositivo, é preciso escanear o QR code de novo.

Esses riscos são aceitáveis numa demonstração e inaceitáveis em produção. Por isso a seção abaixo existe.

## Caminho para produção

Se o projeto um dia for para produção, o WAHA precisa sair. A sugestão é a **WhatsApp Business Cloud API** da Meta, o canal oficial:

1. **Conta:** criar um app no Meta Business Manager, verificar a empresa e registrar um número comercial dedicado.
2. **Credencial:** usar um token permanente de *System User*, não o token temporário do painel. Ele entra como segredo no `.env`, e o sistema deve falhar na inicialização se estiver ausente (princípio do ADR-005).
3. **Formato da mensagem:** existem dois caminhos.
   - Mensagem de texto: preserva as quebras de linha, mas só chega a quem escreveu para o número da empresa nas últimas 24 horas (fora disso, código 131047).
   - Template aprovado: dispensa a janela, mas os parâmetros não aceitam quebra de linha. O relatório precisaria ser desenhado para o template, ou enviado como documento (PDF) anexado a um template curto.
4. **Status de entrega:** webhook de status (`sent`, `delivered`, `read`, `failed`) atualizando a execução, que hoje termina em `ENVIADO`.
5. **Código:** implementar um `CloudApiSender` em `infra/whatsapp.py` para o mesmo `WhatsAppSender`, com um novo valor em `WHATSAPP_PROVIDER`. Domínio, serviço e API não mudam.

Intermediários oficiais (Twilio, 360dialog, Gupshup) usam a mesma Cloud API por baixo. Valem a pena se a concessionária preferir não lidar com o Meta Business diretamente, pagando pelo repasse.

## Alternativas consideradas

- **Manter a Cloud API:** era o caminho de produção, mas tornava a demonstração frágil por burocracia que o projeto não precisa.
- **Evolution API:** parecida com o WAHA e popular no Brasil, mas a v2 exige Postgres, o que pesa o compose sem trazer ganho para a demonstração.
- **Playwright no WhatsApp Web:** reaproveitaria o navegador do robô, mas depende do DOM do site, exige navegador visível no primeiro login (impossível no container, ver ADR-007) e não pode ser feito em TDD.
- **Link `wa.me`:** exige um humano apertando "enviar", então não é envio automatizado.
