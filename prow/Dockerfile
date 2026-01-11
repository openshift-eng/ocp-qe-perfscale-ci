FROM python:3.11.8-slim-bookworm

LABEL vendor="Red Hat Inc." maintainer="OCP QE Team"

# Install required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tar \
    gzip \
    jq \
    gettext-base \
    uuid-runtime \
    openssh-client \
    sshpass \
    iputils-ping \
    ncat \
    rsync \
    libcap2-bin \
    bash \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl
RUN curl -sSL https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-linux-amd64-rhel8.tar.gz \
    | tar -xzf - \
    && mv kubectl /bin

# Python tooling
RUN python -m pip install --upgrade pip \
    && pip install virtualenv jq

# Fix ping capabilities (optional, often unnecessary in containers)
RUN setcap -r /bin/ping || true

# Install rosa
RUN curl -sSL $(curl -sSL https://api.github.com/repos/openshift/rosa/releases/latest \
    | jq -r '.assets[] | select(.name=="rosa_Linux_x86_64.tar.gz") | .browser_download_url') \
    | tar -xzf - \
    && mv rosa /bin \
    && chmod 755 /bin/rosa

# Install ocm
RUN curl -sSL $(curl -sSL https://api.github.com/repos/openshift-online/ocm-cli/releases/latest \
    | jq -r '.assets[] | select(.name=="ocm-linux-amd64") | .browser_download_url') \
    -o /bin/ocm \
    && chmod 755 /bin/ocm
