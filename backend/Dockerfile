# Image de l'API. Elle sert aussi à lancer les migrations et à créer les comptes.

FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

# Le dossier des fichiers (spec 024, ADR-0010) appartient à l'utilisateur de l'API : un volume Docker neuf hérite de ce
# propriétaire au premier montage, et c'est le seul endroit inscriptible d'un conteneur en lecture seule.
RUN useradd --create-home --uid 1000 api && mkdir -p /donnees/fichiers && chown api:api /donnees/fichiers
USER api
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
