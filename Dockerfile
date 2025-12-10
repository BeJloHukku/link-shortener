FROM python:3.13-slim AS builder

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY src ./src
COPY static ./static 

EXPOSE 8000

ENV PATH="/app/.venv/bin:$PATH"


CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
