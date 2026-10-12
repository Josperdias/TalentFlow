FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends antiword && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --home /app talentflow
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY scripts ./scripts
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN mkdir -p /app/private_uploads && chown -R talentflow /app && chmod +x /app/docker-entrypoint.sh
USER talentflow
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health',timeout=4)"
ENTRYPOINT ["/app/docker-entrypoint.sh"]
