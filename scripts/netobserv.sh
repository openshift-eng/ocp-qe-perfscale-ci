#!/usr/bin/env bash

SCRIPTS_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
export DEFAULT_SC=$(oc get storageclass -o=jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}')

deploy_netobserv() {
  echo "====> Deploying NetObserv"
  export NETOBSERV_CHANNEL='stable'
  export NETOBSERV_SOURCE=''
  if [[ -z $INSTALLATION_SOURCE ]]; then
    echo "INSTALLATION_SOURCE env variable is unset. Either it can be set to 'Official', 'Internal', 'OperatorHub', or 'Source' if you intend to use the 'deploy_netobserv' function". Default is 'Internal'
    echo "Using 'Internal' as INSTALLATION_SOURCE"
    deploy_downstream_catalogsource
    NETOBSERV_SOURCE="netobserv-downstream-testing"
  elif [[ $INSTALLATION_SOURCE == "Official" ]]; then
    echo "Using 'Official' as INSTALLATION_SOURCE"
    NETOBSERV_SOURCE="redhat-operators"
  elif [[ $INSTALLATION_SOURCE == "Internal" ]]; then
    echo "Using 'Internal' as INSTALLATION_SOURCE"
    deploy_downstream_catalogsource
    NETOBSERV_SOURCE="netobserv-downstream-testing"
  elif [[ $INSTALLATION_SOURCE == "OperatorHub" ]]; then
    echo "Using 'OperatorHub' as INSTALLATION_SOURCE"
    NETOBSERV_CHANNEL="latest"
    NETOBSERV_SOURCE="community-operators"
  elif [[ $INSTALLATION_SOURCE == "Source" ]]; then
    echo "Using 'Source' as INSTALLATION_SOURCE"
    deploy_upstream_catalogsource
    NETOBSERV_CHANNEL="latest"
    NETOBSERV_SOURCE="netobserv-upstream-testing"
  else
    echo "'$INSTALLATION_SOURCE' is not a valid value for INSTALLATION_SOURCE"
    echo "Please set INSTALLATION_SOURCE env variable to either 'Official', 'Internal', 'OperatorHub', or 'Source' if you intend to use the 'deploy_netobserv' function"
    echo "Don't forget to source 'netobserv.sh' again after doing so!"
    exit 1
  fi

  echo "====> Creating openshift-netobserv-operator namespace and OperatorGroup"
  oc apply -f $SCRIPTS_DIR/netobserv/netobserv-ns_og.yaml
  echo "====> Creating NetObserv subscription"
  oc process --ignore-unknown-parameters=true -f "$SCRIPTS_DIR"/netobserv/netobserv-subscription.yaml -p NETOBSERV_CHANNEL=$NETOBSERV_CHANNEL NETOBSERV_SOURCE=$NETOBSERV_SOURCE -n default -o yaml >/tmp/netobserv-sub.yaml
  oc apply -n openshift-netobserv-operator -f /tmp/netobserv-sub.yaml
  sleep 60
  oc wait --timeout=180s --for=condition=ready pod -l app=netobserv-operator -n openshift-netobserv-operator
  while :; do
    oc get crd/flowcollectors.flows.netobserv.io && break
    sleep 1
  done

  echo "====> Patch CSV so that DOWNSTREAM_DEPLOYMENT is set to 'true'"
  CSV=$(oc get csv -n openshift-netobserv-operator | egrep -i "net.*observ" | awk '{print $1}')
  oc patch csv/$CSV -n openshift-netobserv-operator --type=json -p "[{"op": "replace", "path": "/spec/install/spec/deployments/0/spec/template/spec/containers/0/env/3/value", "value": 'true'}]"
}

createFlowCollector() {
  templateParams=$*
  echo "====> Creating Flow Collector"
  oc process --ignore-unknown-parameters=true -f "$SCRIPTS_DIR"/netobserv/flows_v1beta2_flowcollector.yaml $templateParams -n default -o yaml >/tmp/flowcollector.yaml
  oc apply -f /tmp/flowcollector.yaml
  waitForFlowcollectorReady
}

waitForFlowcollectorReady() {
  echo "====> Waiting for eBPF pods to be ready"
  while :; do
    oc get daemonset netobserv-ebpf-agent -n netobserv-privileged && break
    sleep 1
  done
  sleep 60
  oc wait --timeout=1200s --for=condition=ready pod -l app=netobserv-ebpf-agent -n netobserv-privileged
  oc wait --timeout=1200s --for=condition=ready flowcollector cluster
}

patch_netobserv() {
  COMPONENT=$1
  IMAGE=$2
  CSV=$(oc get csv -n openshift-netobserv-operator | grep -iE "net.*observ" | awk '{print $1}')
  if [[ -z "$COMPONENT" || -z "$IMAGE" ]]; then
    echo "Specify COMPONENT and IMAGE to be patched to existing CSV deployed"
    exit 1
  fi

  if [[ "$COMPONENT" == "ebpf" ]]; then
    echo "====> Patching eBPF image"
    PATCH="[{\"op\": \"replace\", \"path\": \"/spec/install/spec/deployments/0/spec/template/spec/containers/0/env/0/value\", \"value\": \"$IMAGE\"}]"
  elif [[ "$COMPONENT" == "flp" ]]; then
    echo "====> Patching FLP image"
    PATCH="[{\"op\": \"replace\", \"path\": \"/spec/install/spec/deployments/0/spec/template/spec/containers/0/env/1/value\", \"value\": \"$IMAGE\"}]"
  elif [[ "$COMPONENT" == "plugin" ]]; then
    echo "====> Patching Plugin image"
    PATCH="[{\"op\": \"replace\", \"path\": \"/spec/install/spec/deployments/0/spec/template/spec/containers/0/env/2/value\", \"value\": \"$IMAGE\"}]"
  else
    echo "Use component ebpf, flp, plugin, operator as component to patch or to have metrics populated for upstream installation to cluster prometheus"
    exit 1
  fi

  oc patch csv/$CSV -n openshift-netobserv-operator --type=json -p="$PATCH"

  if [[ $? != 0 ]]; then
    echo "failed to patch $COMPONENT with $IMAGE"
    exit 1
  fi
}
get_loki_channel() {
  catalog_label=$1
  channels=$(oc get packagemanifests -l catalog="$catalog_label" -n openshift-marketplace -o jsonpath='{.items[?(@.metadata.name=="loki-operator")].status.channels[*].name}')

  # this works only on bash shell, read command options are different between zsh (commonly used for OSX) and bash shell
  read -r -a channels_arr <<< $channels
  len=${#channels_arr[@]}
  # use the latest channel
  echo "${channels_arr[$len-1]}"
}

waitForResources(){
  resources=$1
  timeout=0
  rc=1
  while [ $timeout -lt 180 ]; do
    status=$(oc get $resources -o jsonpath='{.status.conditions[0].type}' -n netobserv)
    if [[ $status == "Ready" ]]; then
      rc=0
      echo $rc
    fi
    sleep 30
    timeout=$((timeout+30))
  done
  echo $rc
}

deploy_lokistack() {
  echo "====> Deploying LokiStack"
  echo "====> Creating NetObserv Project (if it does not already exist)"
  oc new-project netobserv || true

  echo "====> Creating openshift-operators-redhat Namespace and OperatorGroup"
  oc apply -f $SCRIPTS_DIR/loki/loki-operatorgroup.yaml

  echo "====> Creating netobserv-downstream-testing CatalogSource (if applicable) and Loki Operator Subscription"
  export LOKI_CHANNEL=''
  export LOKI_SOURCE=''
  if [[ $LOKI_OPERATOR == "Unreleased" ]]; then
    deploy_downstream_catalogsource
    LOKI_SOURCE="qe-app-registry"
  else
    LOKI_SOURCE="redhat-operators"
  fi
  
  LOKI_CHANNEL=$(get_loki_channel $LOKI_SOURCE)
  if [ -z "${LOKI_CHANNEL}" ]; then
    echo "====> Could not determine loki-operator subscription channel, exiting!!!!"
    return 1
  fi

  echo "====> Using Loki chanel ${LOKI_CHANNEL} to subscribe"
  oc process --ignore-unknown-parameters=true -f $SCRIPTS_DIR/loki/loki-subscription.yaml -p LOKI_CHANNEL=$LOKI_CHANNEL LOKI_SOURCE=$LOKI_SOURCE -n default -o yaml >/tmp/loki-sub.yaml
  oc apply -n openshift-operators-redhat -f /tmp/loki-sub.yaml

  echo "====> Generate S3_BUCKET_NAME"
  RAND_SUFFIX=$(tr </dev/urandom -dc 'a-z0-9' | fold -w 6 | head -n 1 || true)
  if [[ $WORKLOAD == "None" ]] || [[ -z $WORKLOAD ]]; then
    export S3_BUCKET_NAME="netobserv-ocpqe-$USER-$RAND_SUFFIX"
  else
    export S3_BUCKET_NAME="netobserv-ocpqe-$USER-$WORKLOAD-$RAND_SUFFIX"
  fi

  S3_BUCKET_NAME+="-preserve"
  echo "====> S3_BUCKET_NAME is $S3_BUCKET_NAME"

  echo "====> Creating S3 secret for Loki"
  $SCRIPTS_DIR/deploy-loki-aws-secret.sh $S3_BUCKET_NAME
  sleep 60
  while :; do
    oc wait --timeout=180s --for=condition=ready pod -l app.kubernetes.io/name=loki-operator -n openshift-operators-redhat && break
    sleep 1
  done

  echo "====> Determining LokiStack config"
  export SIZE=''
  if [[ $LOKISTACK_SIZE == "1x.demo" ]]; then
    SIZE="1x.demo"
  elif [[ $LOKISTACK_SIZE == "1x.extra-small" ]]; then
    SIZE="1x.extra-small"
  elif [[ $LOKISTACK_SIZE == "1x.small" ]]; then
    SIZE="1x.small"
  elif [[ $LOKISTACK_SIZE == "1x.medium" ]]; then
    SIZE="1x.medium"
  else
    echo "====> No LokiStack config was found - using '1x.extra-small'"
    echo "====> To set config, set LOKISTACK_SIZE variable to either '1x.extra-small', '1x.small', or '1x.medium'"
    SIZE="1x.extra-small"
  fi

  echo "====> Creating LokiStack"
  oc process --ignore-unknown-parameters=true -f $SCRIPTS_DIR/loki/lokistack.yaml -p SIZE=$SIZE DEFAULT_SC=$DEFAULT_SC -n default -o yaml >/tmp/lokiStack.yaml
  oc apply -f /tmp/lokiStack.yaml
  sleep 30
  echo "====> Waiting lokistack to be ready"
  lokistackReady=$(waitForResources "lokistack/lokistack")
  if [ "${lokistackReady}" == 1 ]; then
    echo "LokiStack did not become Ready after 180 secs!!!"
    return 1
  fi
  echo "====> Configuring Loki rate limit alert"
  oc apply -f $SCRIPTS_DIR/loki/loki-ratelimit-alert.yaml
}

deploy_downstream_catalogsource() {
  echo "====> Creating brew-registry ImageContentSourcePolicy"
  oc apply -f $SCRIPTS_DIR/icsp.yaml

  echo "====> Determining CatalogSource config"
  if [[ -z $DOWNSTREAM_IMAGE ]]; then
    CLUSTER_VERSION=$(oc get clusterversion/version -o jsonpath='{.spec.channel}' | cut -d'-' -f 2)
    export CLUSTER_VERSION
    echo "====> No image config was found; will use quay.io/openshift-qe-optional-operators/aosqe-index:v${CLUSTER_VERSION} as index image"
    DOWNSTREAM_IMAGE="quay.io/openshift-qe-optional-operators/aosqe-index:v${CLUSTER_VERSION}"
    export DOWNSTREAM_IMAGE
  else
    echo "====> Using image $DOWNSTREAM_IMAGE for CatalogSource"
  fi

  CatalogSource_CONFIG=$SCRIPTS_DIR/catalogsources/netobserv-downstream-testing.yaml
  TMP_CATALOGCONFIG=/tmp/catalogconfig.yaml
  envsubst <$CatalogSource_CONFIG >$TMP_CATALOGCONFIG

  echo "====> Creating netobserv-downstream-testing CatalogSource"
  oc apply -f $TMP_CATALOGCONFIG
  sleep 30
  oc wait --timeout=180s --for=condition=ready pod -l olm.catalogSource=netobserv-downstream-testing -n openshift-marketplace
}

deploy_upstream_catalogsource() {
  echo "====> Determining CatalogSource config"
  if [[ -z $UPSTREAM_IMAGE ]]; then
    echo "====> No image config was found - using main"
    echo "====> To set config, set UPSTREAM_IMAGE variable to desired endpoint"
    export UPSTREAM_IMAGE="quay.io/netobserv/network-observability-operator-catalog:v0.0.0-main"
  else
    echo "====> Using image $UPSTREAM_IMAGE for CatalogSource"
  fi

  CatalogSource_CONFIG=$SCRIPTS_DIR/catalogsources/netobserv-upstream-testing.yaml
  TMP_CATALOGCONFIG=/tmp/catalogconfig.yaml
  envsubst <$CatalogSource_CONFIG >$TMP_CATALOGCONFIG

  echo "====> Creating netobserv-upstream-testing CatalogSource from the main bundle"
  oc apply -f $TMP_CATALOGCONFIG
  sleep 30
  oc wait --timeout=180s --for=condition=ready pod -l olm.catalogSource=netobserv-upstream-testing -n openshift-marketplace
}

deploy_kafka() {
  echo "====> Deploying Kafka"
  oc create namespace netobserv --dry-run=client -o yaml | oc apply -f -
  echo "====> Creating amq-streams Subscription"
  oc apply -f $SCRIPTS_DIR/amq-streams/amq-streams-subscription.yaml
  sleep 60
  oc wait --timeout=180s --for=condition=ready pod -l name=amq-streams-cluster-operator -n openshift-operators

  # update AMQStreams operator memory limit to 1G as current limits of 384Mi is not enough for 250 nodes scenario
  CSV_NAME=$(oc get csv -n openshift-operators -l operators.coreos.com/amq-streams.openshift-operators= -o jsonpath='{.items[].metadata.name}')
  oc -n openshift-operators patch csv $CSV_NAME --type=json -p "[{"op": "replace", "path": "/spec/install/spec/deployments/0/spec/template/spec/containers/0/resources/limits/memory", "value": "1Gi"}]"
  
  echo "====> Creating kafka-metrics ConfigMap and kafka-resources-metrics PodMonitor"
  oc apply -f "https://raw.githubusercontent.com/netobserv/documents/main/examples/kafka/metrics-config.yaml" -n netobserv
  echo "====> Creating kafka-cluster Kafka"
  curl -s -L "https://raw.githubusercontent.com/netobserv/documents/main/examples/kafka/default.yaml" | envsubst | oc apply -n netobserv -f -

  echo "====> Creating network-flows KafkaTopic"
  if [[ -z $TOPIC_PARTITIONS ]]; then
    echo "====> No topic partitions config was found - using 6"
    echo "====> To set config, set TOPIC_PARTITIONS variable to desired number"
    export TOPIC_PARTITIONS=6
  fi
  KAFKA_TOPIC=$SCRIPTS_DIR/amq-streams/kafkaTopic.yaml
  TMP_KAFKA_TOPIC=/tmp/topic.yaml
  envsubst <$KAFKA_TOPIC >$TMP_KAFKA_TOPIC
  oc apply -f $TMP_KAFKA_TOPIC -n netobserv
  sleep 120
  oc wait --timeout=180s --for=condition=ready kafkatopic network-flows -n netobserv
}

delete_s3() {
  S3_BUCKET_NAME=$(oc get secrets/s3-secret -n netobserv -o jsonpath='{.data.bucketnames}' | base64 -d)
  echo "====> Getting S3 Bucket Name"
  if [[ -z $S3_BUCKET_NAME ]]; then
    echo "====> Could not get S3 Bucket Name"
  else
    echo "====> Got $S3_BUCKET_NAME"
    echo "====> Deleting AWS S3 Bucket"
    while :; do
      aws s3 rb s3://$S3_BUCKET_NAME --force && break
      sleep 1
    done
    echo "====> AWS S3 Bucket $S3_BUCKET_NAME deleted"
  fi
}

delete_lokistack() {
  echo "====> Deleting LokiStack"
  oc delete --ignore-not-found lokistack/lokistack -n netobserv
}


delete_kafka() {
  echo "====> Deleting Kafka"
  oc delete --ignore-not-found kafkaTopic/network-flows -n netobserv
  oc delete --ignore-not-found kafka/kafka-cluster -n netobserv
  oc delete --ignore-not-found -f $SCRIPTS_DIR/amq-streams/amq-streams-subscription.yaml
  oc delete --ignore-not-found csv -l operators.coreos.com/amq-streams.openshift-operators -n openshift-operators
}

delete_flowcollector() {
  echo "====> Deleting Flow Collector"
  # note 'cluster' is the default Flow Collector name, but that may not always be the case
  oc delete --ignore-not-found flowcollector/cluster
}

delete_netobserv_operator() {
  echo "====> Deleting all NetObserv resources"
  oc delete --ignore-not-found sub/netobserv-operator -n openshift-netobserv-operator
  oc delete --ignore-not-found csv -l operators.coreos.com/netobserv-operator.openshift-netobserv-operator= -n openshift-netobserv-operator
  oc delete --ignore-not-found crd/flowcollectors.flows.netobserv.io
  oc delete --ignore-not-found -f $SCRIPTS_DIR/netobserv/netobserv-ns_og.yaml
  echo "====> Deleting netobserv-upstream-testing and netobserv-downstream-testing CatalogSource (if applicable)"
  oc delete --ignore-not-found catalogsource/netobserv-upstream-testing -n openshift-marketplace
  oc delete --ignore-not-found catalogsource/netobserv-downstream-testing -n openshift-marketplace
}

delete_loki_operator() {
  echo "====> Deleting Loki Operator Subscription and CSV"
  oc delete --ignore-not-found sub/loki-operator -n openshift-operators-redhat
  oc delete --ignore-not-found csv -l operators.coreos.com/loki-operator.openshift-operators-redhat -n openshift-operators-redhat
}

nukeobserv() {
  echo "====> Nuking NetObserv and all related resources"
  delete_kafka
  if [[ $LOKI_OPERATOR != "None" ]]; then
    delete_lokistack
    delete_loki_operator
    delete_s3
  fi
  delete_flowcollector
  delete_netobserv_operator
  # seperate step as multiple different operators use this namespace
  oc delete project netobserv
}
