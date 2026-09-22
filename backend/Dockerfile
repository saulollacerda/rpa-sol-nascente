# Imagem oficial do Playwright: já traz o Chromium e as bibliotecas de
# sistema que ele exige. A tag precisa acompanhar a versão do pacote
# playwright no uv.lock — browsers e biblioteca têm que casar.
FROM mcr.microsoft.com/playwright/python:v1.63.0-noble AS base

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependências antes do código: a camada só é refeita quando o lock muda,
# e não a cada edição de arquivo.
COPY pyproject.toml uv.lock ./


FROM base AS dev
RUN uv sync --frozen --no-install-project
COPY app ./app
COPY tests ./tests
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


FROM base AS prod
RUN uv sync --frozen --no-install-project --no-dev
COPY app ./app
USER pwuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
