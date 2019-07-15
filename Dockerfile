FROM debian:buster-slim

LABEL maintainer="Rémi Duraffort <remi.duraffort@linaro.org>"

ENV DEBIAN_FRONTEND noninteractive

WORKDIR /app/

# Add ReactOBus sources
COPY share/entrypoint.sh /entrypoint.sh
COPY reactobus /app/reactobus

# Install dependencies
RUN apt-get update -q ;\
    apt-get install --no-install-recommends --yes python3-setproctitle python3-sqlalchemy python3-yaml python3-zmq ;\
    # Cleanup
    apt-get clean ;\
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/entrypoint.sh"]
