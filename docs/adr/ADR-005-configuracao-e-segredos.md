# ADR-005 — Configuração e segredos

**Status:** Aceito · 2026-09-22 · parte de WhatsApp substituída pelo [ADR-009](ADR-009-waha-para-demonstracao.md) em 2026-09-23

> As variáveis `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` e `WHATSAPP_API_VERSION` e a validação do token na inicialização saíram junto com a Cloud API. A tabela vigente das variáveis de WhatsApp está no ADR-009; as demais regras deste ADR seguem valendo.

## Contexto

O enunciado exige que credenciais, tokens e chaves fiquem **fora do código-fonte**, e lista "documentação e segurança básica" entre os critérios de avaliação.

O projeto lida com pelo menos um segredo real — o token da Cloud API da Meta — e com um dado pessoal, o número de WhatsApp do destinatário. Ambos vão para um repositório que será entregue a terceiros para avaliação, o que torna um vazamento acidental um problema concreto, não hipotético.

## Decisão

Configuração centralizada em `backend/app/config.py` usando **`pydantic-settings`**, que lê variáveis de ambiente e um arquivo `.env` local.

Nenhum módulo lê `os.environ` diretamente. Todo acesso passa pelo objeto `Settings`, o que dá validação de tipo na inicialização e um único lugar para auditar o que o sistema consome.

`.env.example` é versionado, com todas as chaves presentes e **sem nenhum valor real**. `.env` está no `.gitignore` desde o primeiro commit.

### Variáveis

| Variável | Segredo | Descrição |
|---|---|---|
| `WHATSAPP_PROVIDER` | não | `cloud_api` ou `fake` |
| `WHATSAPP_TOKEN` | **sim** | token de acesso da Graph API |
| `WHATSAPP_PHONE_NUMBER_ID` | não | identificador do número remetente |
| `WHATSAPP_DESTINATARIO` | dado pessoal | telefone padrão em formato E.164 |
| `WHATSAPP_API_VERSION` | não | versão da Graph API, padrão `v23.0` |
| `BCB_BASE_URL` | não | URL da fonte, parametrizada para permitir fixture em teste |
| `DATABASE_URL` | não | padrão `sqlite:///./data/execucoes.db` |
| `DATA_DIR` | não | diretório dos artefatos baixados |
| `PLAYWRIGHT_HEADLESS` | não | `false` ajuda a depurar e a demonstrar a navegação |
| `LOG_LEVEL` | não | padrão `INFO` |

### Regras operacionais

O sistema **falha na inicialização** se `WHATSAPP_PROVIDER=cloud_api` e o token ou o `WHATSAPP_PHONE_NUMBER_ID` estiverem ausentes. Falhar cedo e explicitamente é melhor do que descobrir a ausência da credencial no meio de uma execução, depois de já ter baixado os arquivos.

Tokens nunca aparecem em log. O logging estruturado tem uma lista de chaves sensíveis que são mascaradas antes da serialização, porque o risco real não é alguém imprimir o token de propósito — é um `log.debug` da configuração inteira vazar tudo de uma vez.

Mensagens de erro expostas pela API não repassam o corpo bruto da resposta da Meta, que pode conter fragmentos de credencial.

## Justificativa

`pydantic-settings` foi escolhido em vez de `python-dotenv` puro porque valida tipos e presença na subida do processo. A diferença prática é entre um erro claro ao iniciar e um `None` silencioso que só estoura três camadas abaixo.

`PLAYWRIGHT_HEADLESS` ser configurável não é detalhe: rodar com o browser visível durante a apresentação mostra a automação navegando de verdade, o que é mais convincente do que descrevê-la.

## Consequências

**Positivas** — nenhum segredo no repositório; configuração validada e centralizada; `.env.example` funciona como documentação executável do que precisa ser preenchido.

**Negativas** — `.env` em texto puro no disco é adequado para desenvolvimento, não para produção, onde o correto seria um gerenciador de segredos. Fica registrado como o primeiro item a mudar na transição para produção.

## Alternativas consideradas

**Constantes em um `settings.py` versionado.** Descartada de imediato: é exatamente o que o enunciado proíbe.

**Apenas variáveis de ambiente, sem `.env`.** Mais próximo do ideal de produção, mas obrigaria quem for avaliar o projeto a exportar variáveis manualmente antes de rodar. O `.env` com `.env.example` versionado atinge o mesmo objetivo de segurança com muito menos atrito.

**Gerenciador de segredos (Vault, AWS Secrets Manager).** Desproporcional para um projeto local de demonstração.
