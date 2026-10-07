FROM python:3.11-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml ./
COPY flask/ ./flask/
COPY mcp_servers/ ./mcp_servers/

RUN python -m pip install --no-cache-dir . \
    && groupadd --gid 10001 chillbot \
    && useradd --uid 10001 --gid chillbot --no-create-home chillbot

USER chillbot

EXPOSE 5000

CMD ["gunicorn", "--chdir", "flask", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "app:app"]
