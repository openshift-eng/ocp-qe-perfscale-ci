FROM quay.io/openshifttest/python:3.9

LABEL vendor="Red Hat Inc." maintainer="OCP QE Team"

RUN curl -sSL https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-linux-amd64-rhel8.tar.gz | tar -xvzf -  &&\
    mv kubectl /bin &&\
    mv oc /bin

RUN apt-get update && apt-get install -y gettext-base uuid-runtime jq openssh-client sshpass && \
    ln -s /bin/bash /usr/bin/bash && /usr/local/bin/python -m pip install --upgrade pip && pip install virtualenv jq

RUN curl -sSL $(curl -sSL https://api.github.com/repos/openshift/rosa/releases/latest | jq -r ".assets[] | select(.name == \"rosa_Linux_x86_64.tar.gz\") | .browser_download_url") | tar xvzf - &&\
    mv rosa /bin && chmod 777 /bin/rosa

RUN curl -sSL $(curl -sSL https://api.github.com/repos/openshift-online/ocm-cli/releases/latest | jq -r ".assets[] | select(.name == \"ocm-linux-amd64\") | .browser_download_url") --output /bin/ocm && chmod 777 /bin/ocm
