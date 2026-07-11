# NOTE: This container runs as root — required to access the Docker socket.
# To harden it: create a non-root user and add it to the docker group
# with the correct GID of the host machine.
#
# WARNING: Mounting /var/run/docker.sock grants effective root access to the host.
# Do not expose the API publicly without a reverse proxy with authentication.

FROM python:3.12-slim

WORKDIR /app

# rpm: reads NDB databases (openSUSE) and serves as the 1st method for BerkeleyDB (Rocky 8, CentOS 7, UBI8)
# db-util (db_dump): fallback method for BerkeleyDB, recent rpm builds can no longer read it natively
RUN apt-get update \
    && apt-get install -y --no-install-recommends rpm db-util \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry==2.1.3 --no-cache-dir

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --without dev --no-interaction --no-ansi

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
