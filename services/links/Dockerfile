FROM python:3.14.8-slim AS builder

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen

FROM python:3.14.8-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY src ./src

EXPOSE 8000

ENV PATH="/app/.venv/bin:$PATH"


CMD ["uvicorn", "links.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
