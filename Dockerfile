# NOTE: Ce container tourne en root — requis pour accéder au socket Docker.
# Pour le durcir : créer un utilisateur non-root et l'ajouter au groupe docker
# avec le bon GID de la machine hôte.
#
# WARNING: Monter /var/run/docker.sock donne un accès root effectif à l'hôte.
# Ne pas exposer l'API publiquement sans un reverse proxy avec authentification.

FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry==2.1.3 --no-cache-dir

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --without dev --no-interaction --no-ansi

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
