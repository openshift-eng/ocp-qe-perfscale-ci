#!/usr/bin/env bash
# check whether it's running on jenkins or prow
TOOLS_DIR=/tmp/bin
if [[ -n $JENKINS_HOME ]]; then
    # when running on jenkins
    mkdir -p ~/.kube
    cp ${WORKSPACE}/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
    # source from 4.16 because jenkins agent are on RHEL 8
    curl -sL "https://mirror2.openshift.com/pub/openshift-v4/x86_64/clients/ocp/latest-4.16/opm-linux.tar.gz" -o opm-linux.tar.gz
    tar xf opm-linux.tar.gz
    OPM_BIN="./opm-rhel8"
else
    mkdir -p ${TOOLS_DIR}
    export PATH=${TOOLS_DIR}:${PATH}
    curl -L --retry 5 https://github.com/operator-framework/operator-registry/releases/download/v1.26.2/linux-amd64-opm -o ${TOOLS_DIR}/opm && chmod +x ${TOOLS_DIR}/opm
    OPM_BIN=$(which opm)
fi
set -x

RELEASE=$(oc get pods -l app=netobserv-operator -o jsonpath="{.items[*].spec.containers[0].env[?(@.name=='OPERATOR_CONDITION_NAME')].value}" -A | cut -d 'v' -f 3)
catalogName=$(oc get sub/netobserv-operator -n openshift-netobserv-operator -o jsonpath='{.spec.source}')
catalogSourceNS=$(oc get sub/netobserv-operator -n openshift-netobserv-operator -o jsonpath='{.spec.sourceNamespace}')
CATALOG_IMAGE=$(oc get catalogsource/"$catalogName" -n "$catalogSourceNS"  -o jsonpath='{.spec.image}')
opm_out=$($OPM_BIN alpha list bundles "$CATALOG_IMAGE" netobserv-operator | grep "$RELEASE")
BUNDLE_IMAGE=${opm_out##* }
bundle_tag=$(oc image info $BUNDLE_IMAGE -o json --filter-by-os linux/amd64 | jq '.config.config.Labels["vcs-ref"]')
CREATED_DATE=$(oc image info $BUNDLE_IMAGE -o json --filter-by-os linux/amd64 | jq '.config.created')
bundle_tag=${bundle_tag//\"/}
# remove quotes and milliseconds from created date
CREATED_DATE=${CREATED_DATE//\"/}
CREATED_DATE=${CREATED_DATE//\./}
short_tag="${bundle_tag:0:7}"
echo "$RELEASE-$CREATED_DATE-$short_tag"
