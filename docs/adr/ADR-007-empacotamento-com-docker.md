# ADR-007 — Empacotamento e isolamento com Docker

**Status:** Aceito · 2026-09-22

## Contexto

A solução depende de um navegador real ([ADR-002](ADR-002-fonte-bcb-e-estrategia-de-rpa.md)), e é aí que "funciona na minha máquina" costuma aparecer. O Chromium do Playwright exige um conjunto de bibliotecas de sistema — `libnss3`, `libatk`, `libgbm` e outras — cuja ausência produz erros que não se parecem com o problema real. Instalar isso na mão varia entre macOS, distribuições Linux e WSL.

Some-se a dependência de duas toolchains ([ADR-001](ADR-001-stack-e-arquitetura.md)): Python com `uv` e, futuramente, Node para o frontend. Quem for avaliar o projeto teria que montar as duas antes de ver qualquer coisa rodando.

Há também um requisito de correção, não só de conveniência: a **versão do pacote `playwright` e a dos binários de navegador precisam casar**. Se divergirem, a automação falha de formas obscuras.

## Decisão

Empacotar o backend em Docker, a partir da **imagem oficial do Playwright**, com orquestração por Docker Compose.

```
mcr.microsoft.com/playwright/python:v1.63.0-noble
```

A tag acompanha a versão do pacote `playwright` no `uv.lock` — alterar uma exige alterar a outra.

### Dois alvos no mesmo Dockerfile

| Alvo | Dependências | Código | Usuário | Uso |
|---|---|---|---|---|
| `dev` | com as de desenvolvimento | montado do host | root | desenvolvimento e testes |
| `prod` | sem as de desenvolvimento | copiado na imagem | `pwuser` | demonstração e produção |

As dependências são instaladas **antes** de copiar o código, para que a camada só seja refeita quando o `uv.lock` mudar, e não a cada edição de arquivo.

### Volumes

`./backend/data` é montado em `/app/data`. É onde ficam o cache de ZIPs do [ADR-006](ADR-006-estrategia-de-cache-e-revalidacao.md) e o banco SQLite do [ADR-004](ADR-004-persistencia-e-idempotencia.md) — ambos precisam sobreviver ao ciclo de vida do container. Optou-se por *bind mount* em vez de volume nomeado para que os arquivos fiquem visíveis no host, o que ajuda a depurar e a demonstrar.

O `DATABASE_URL` e o `DATA_DIR` são sobrescritos no Compose, porque dentro do container os caminhos são absolutos.

### Segredos

O `.env` entra por `env_file` com `required: false`, nunca copiado para a imagem — o `.dockerignore` o exclui explicitamente. Uma imagem sem `.env` sobe normalmente, com os defaults do [ADR-005](ADR-005-configuracao-e-segredos.md), que usam o adapter fake de WhatsApp.

## Verificação

Tudo abaixo foi executado, não presumido:

| Verificação | Resultado |
|---|---|
| Build do alvo `dev` | ✅ |
| Suíte de testes dentro do container | ✅ 6 passed |
| Chromium abre e renderiza | ✅ `chromium-1243` |
| `GET /health` pela porta publicada | ✅ `{"status":"ok","versao":"0.1.0"}` |
| Volume sobrevive a `restart` | ✅ |
| Arquivos do volume visíveis no host | ✅ |
| Alvo `prod` roda como não-root | ✅ `pwuser` |

## Consequências

**Positivas** — um comando (`docker compose up`) substitui instalar Python, `uv`, Playwright e as bibliotecas de sistema do Chromium. A paridade entre biblioteca e binários do navegador passa a ser garantida pela imagem. Quem avaliar o projeto não precisa montar ambiente.

**Negativas** — a imagem tem **4,12 GB** (`dev`) e 4,02 GB (`prod`). Quase tudo é o Chromium e suas dependências, herdados da imagem base; pouco disso é código nosso. O primeiro `build` baixa vários gigabytes.

### A tensão com a demonstração ao vivo

O [ADR-005](ADR-005-configuracao-e-segredos.md) registra que `PLAYWRIGHT_HEADLESS=false` permite mostrar a automação navegando, o que é mais convincente do que descrevê-la. **Dentro do container isso não funciona**: não há servidor gráfico, e o Compose força `PLAYWRIGHT_HEADLESS=true`.

Duas saídas, ambas aceitáveis:

1. **Gravar vídeo.** O Playwright grava o contexto do navegador em vídeo. O artefato é até melhor que uma janela ao vivo, porque pode ser repetido e anexado.
2. **Rodar o RPA no host para a demonstração.** O projeto continua executável fora do Docker — o container é uma conveniência, não um acoplamento.

## Alternativas consideradas

**Imagem Python base com `playwright install --with-deps`.** Resultaria numa imagem de tamanho parecido, já que o peso é o navegador, mas exigiria manter à mão a lista de dependências de sistema e a sincronia entre versões. A imagem oficial resolve os dois problemas.

**Conteinerizar apenas para produção, desenvolvendo no host.** Descartado porque o valor principal aqui é justamente eliminar a montagem de ambiente para quem for avaliar o projeto.

**Volume nomeado em vez de bind mount para `data/`.** Mais idiomático em produção, porém esconde os arquivos baixados. Para um projeto que precisa ser demonstrado e explicado, ver o ZIP aparecer no diretório vale mais.
