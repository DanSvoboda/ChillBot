FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml ./

RUN python -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch torchvision \
    && python -m pip install --no-cache-dir .

COPY web/ ./web/
COPY mcp_servers/ ./mcp_servers/

RUN groupadd --gid 10001 chillbot \
    && useradd --uid 10001 --gid chillbot --create-home chillbot \
    && mkdir -p /app/models/varieties /app/data/vector_store \
    && chown -R chillbot:chillbot /app/models /app/data

USER chillbot

EXPOSE 5000 8000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "web.app:app"]
