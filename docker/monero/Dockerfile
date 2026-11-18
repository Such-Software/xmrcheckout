FROM debian:bookworm-slim

ARG MONERO_VERSION=0.18.4.6

RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates curl bzip2 \
  && rm -rf /var/lib/apt/lists/*

# Each tarball's SHA-256 comes from binaryFate's GPG-signed hashes.txt
# (getmonero.org/downloads/hashes.txt; for older releases, its history in
# monero-project/monero-site). Verify that signature against
# utils/gpg_keys/binaryfate.asc in monero-project/monero before adding a version.
# A version without an entry here refuses to build.
RUN set -eux; \
  arch="$(dpkg --print-architecture)"; \
  if [ "$arch" = "amd64" ]; then \
    monero_arch="x64"; \
  elif [ "$arch" = "arm64" ]; then \
    monero_arch="armv8"; \
  else \
    echo "Unsupported architecture: $arch" >&2; \
    exit 1; \
  fi; \
  tarball="monero-linux-${monero_arch}-v${MONERO_VERSION}.tar.bz2"; \
  case "$tarball" in \
    monero-linux-x64-v0.18.4.6.tar.bz2) \
      monero_sha256="60cfc32d39c6fe6c19b23513d02017fe9055d2e412ee4cbc30fa40ba811fe052" ;; \
    monero-linux-armv8-v0.18.4.6.tar.bz2) \
      monero_sha256="d38c9ef8ee1a5d2de32f67d2f46c767c0c5cc3bb23ba7e3dfa9cbb19ceb2c84c" ;; \
    *) \
      echo "No pinned SHA-256 for $tarball; add it to docker/monero/Dockerfile from the signed hashes.txt" >&2; \
      exit 1 ;; \
  esac; \
  curl -fsSL -o /tmp/monero.tar.bz2 \
    "https://downloads.getmonero.org/cli/${tarball}"; \
  echo "${monero_sha256}  /tmp/monero.tar.bz2" | sha256sum -c -; \
  tar -xjf /tmp/monero.tar.bz2 -C /tmp; \
  cp /tmp/monero-*/monerod /usr/local/bin/; \
  cp /tmp/monero-*/monero-wallet-rpc /usr/local/bin/; \
  rm -rf /tmp/monero* /tmp/monero.tar.bz2

COPY entrypoint.sh /usr/local/bin/monero-wallet-rpc-entrypoint
RUN chmod +x /usr/local/bin/monero-wallet-rpc-entrypoint

EXPOSE 18081 18083

ENTRYPOINT ["/usr/local/bin/monero-wallet-rpc-entrypoint"]
