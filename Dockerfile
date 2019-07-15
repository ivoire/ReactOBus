FROM debian:buster-slim

LABEL maintainer="Rémi Duraffort <remi.duraffort@linaro.org>"

ENV DEBIAN_FRONTEND noninteractive

# Install dependencies
RUN apt-get update -q ;\
    apt-get install --no-install-recommends --yes python3-psycopg2 python3-setproctitle python3-sqlalchemy python3-yaml python3-zmq ;\
    # Cleanup
    apt-get clean ;\
    rm -rf /var/lib/apt/lists/*

# Add ReactOBus sources
WORKDIR /app/
COPY share/entrypoint.sh /entrypoint.sh
COPY reactobus /app/reactobus

# Add the entrypoint
ENTRYPOINT ["/entrypoint.sh"]
