FROM registry.access.redhat.com/ubi9/ubi:latest

LABEL vendor="Red Hat Inc." maintainer="OCP QE Team"

COPY --from=docker.io/mikefarah/yq /usr/bin/yq /bin/yq

RUN dnf install -y python3.11 python3.11-pip && ln -s /usr/bin/python3.11 /usr/bin/python && ln -s /usr/bin/pip3.11 /usr/bin/pip

RUN curl -sSL https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-linux-amd64-rhel8.tar.gz | tar -xvzf -  &&\
    mv kubectl /bin

RUN dnf update -y && dnf install -y gettext util-linux jq openssh-clients sshpass iputils nmap-ncat rsync procps-ng git gcc && \
    python3.11 -m pip install --upgrade pip && python3.11 -m pip install virtualenv jq

# Remove capabilities from ping - resolve any symlinks to find actual binary
RUN PING_BIN=$(readlink -f /usr/bin/ping 2>/dev/null || echo /usr/bin/ping) && \
    if [ -f "$PING_BIN" ] && [ ! -L "$PING_BIN" ]; then \
        setcap -r "$PING_BIN" 2>&1 || echo "Warning: Could not remove capabilities from ping (may not be supported)"; \
    fi

RUN curl -sSL $(curl -sSL https://api.github.com/repos/openshift/rosa/releases/latest | jq -r ".assets[] | select(.name == \"rosa_Linux_x86_64.tar.gz\") | .browser_download_url") | tar xvzf - &&\
    mv rosa /bin && chmod 777 /bin/rosa

RUN curl -sSL $(curl -sSL https://api.github.com/repos/openshift-online/ocm-cli/releases/latest | jq -r ".assets[] | select(.name == \"ocm-linux-amd64\") | .browser_download_url") --output /bin/ocm && chmod 777 /bin/ocm
