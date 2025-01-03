#!/usr/bin/env bash
mkdir -p ~/.kube
cp ${WORKSPACE}/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
RELEASE=$(oc get pods -l app=netobserv-operator -o jsonpath='{.items[*].spec.containers[1].env[0].value}' -A | cut -d 'v' -f 3)

# source from 4.12 because jenkins agent are on RHEL 8
curl -sL "https://mirror2.openshift.com/pub/openshift-v4/x86_64/clients/ocp/latest-4.16/opm-linux.tar.gz" -o opm-linux.tar.gz
tar xf opm-linux.tar.gz
BUNDLE_IMAGE=$(./opm-rhel8 alpha list bundles $CATALOG_IMAGE netobserv-operator | grep $RELEASE | awk '{print $5}')
oc image info $BUNDLE_IMAGE -o json --filter-by-os linux/amd64 | jq '.config.config.Labels.url' | awk -F '/' '{print $NF}' | tr '\"' ' '
