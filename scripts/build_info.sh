#!/usr/bin/env bash
set -x
# check whether it's running on jenkins or prow
if [[ -n $JENKINS_HOME ]]; then
    # when running on jenkins
    mkdir -p ~/.kube
    cp ${WORKSPACE}/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
    # source from 4.16 because jenkins agent are on RHEL 8
    curl -sL "https://mirror2.openshift.com/pub/openshift-v4/x86_64/clients/ocp/latest-4.16/opm-linux.tar.gz" -o opm-linux.tar.gz
    tar xf opm-linux.tar.gz
    OPM_BIN="./opm-rhel8"
else
    OPM_BIN=$(which opm)
fi

RELEASE=$(oc get pods -l app=netobserv-operator -o jsonpath="{.items[*].spec.containers[0].env[?(@.name=='OPERATOR_CONDITION_NAME')].value}" -A | cut -d 'v' -f 3)

if [[ -n $DOWNSTREAM_IMAGE ]]; then
    CATALOG_IMAGE=$DOWNSTREAM_IMAGE
else
    echo "===> Set DOWNSTREAM_IMAGE env var to the catalog source image used for netobserv-operator"
    exit 1
fi

BUNDLE_IMAGE=$($OPM_BIN alpha list bundles "$CATALOG_IMAGE" netobserv-operator | grep "$RELEASE" | awk '{print $5}')
bundle_tag=$(oc image info $BUNDLE_IMAGE -o json --filter-by-os linux/amd64 | jq '.config.config.Labels["vcs-ref"]')
CREATED_DATE=$(oc image info $BUNDLE_IMAGE -o json --filter-by-os linux/amd64 | jq '.config.created')
bundle_tag=${bundle_tag//\"/}
# remove quotes and milliseconds from created date
CREATED_DATE=${CREATED_DATE//\"/}
CREATED_DATE=${CREATED_DATE//\./}
echo "$RELEASE-$CREATED_DATE-$bundle_tag"
