#!/bin/bash

export CONSOLE_URL=$(oc get routes console -n openshift-console -o jsonpath='{.spec.host}')

export CLUSTER_NAME=$(oc get machineset -n openshift-machine-api -o=go-template='{{(index (index .items 0).metadata.labels "machine.openshift.io/cluster-api-cluster" )}}')

export BASE_API_URL=$(oc get infrastructure -o jsonpath="{.items[*].status.apiServerURL}")
export TOKEN=$(oc whoami -t)
export NAMESPACE=${NAMESPACE:-default}

oc label ns $NAMESPACE security.openshift.io/scc.podSecurityLabelSync=false pod-security.kubernetes.io/enforce=privileged pod-security.kubernetes.io/audit=privileged pod-security.kubernetes.io/warn=privileged --overwrite

# path for local testing
#dast_tool_path=../rapidast/
dast_tool_path=${DAST_PATH:-./dast_tool}
echo "$CONSOLE_URL"
#curl -k "https://${CONSOLE_URL}/api/kubernetes/openapi/v2" -H "Cookie: openshift-session-token=${TOKEN}"  -H "Accept: application/json"  >> openapi.json
mkdir results 

counter=0
#for api_doc in $(kubectl api-versions); do
for api_doc in ${API_URL_LIST}; do
  echo "api doc $api_doc"
  # export API_URL="https://raw.githubusercontent.com/paigerube14/ocp-qe-perfscale-ci/ssml/apidocs/$api_doc"
  if [[ "$api_doc" == *"/"* ]]; then
    export API_URL="$BASE_API_URL/openapi/v3/apis/$api_doc"
  else   # e.g. 'v1'
    export API_URL="$BASE_API_URL/openapi/v3/api/$api_doc"
  fi
  
  echo "api url: $API_URL"
  #edit rapidast config file
  envsubst < values.yaml.template > $dast_tool_path/helm/chart/value_test.yaml
  helm install rapidast $dast_tool_path/helm/chart -f $dast_tool_path/helm/chart/value_test.yaml

  # wait for pod to be completed or error
  rapidast_pod=$(oc get pods -n default -l job-name=rapidast-job -o name)
  echo "rapidast current pod $rapidast_pod"
  oc wait --for=condition=Ready $rapidast_pod --timeout=120s

  folder_api_name=$(echo "$api_doc" | tr "/" .)
  mkdir results/$folder_api_name

  #oc get $rapidast_pod -n default -o yaml >> results/$folder_api_name/pod_yaml.yaml

  oc get $rapidast_pod -o 'jsonpath={..status.conditions}'
  while [[ $(oc get $rapidast_pod -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') == "True" ]]; do
    echo "sleeping 5"
    sleep 5
    
  done
  
  #cp $dast_tool_path/helm/chart/value_test.yaml results/$folder_api_name/value.yaml

  oc logs $rapidast_pod -n default >> results/$folder_api_name/pod_logs.out

  ./results.sh rapidast-pvc results/$folder_api_name
  ls results

  ls results/$folder_api_name

  phase=$(oc get $rapidast_pod -o jsonpath='{.status.phase}')
  helm uninstall rapidast 
  oc delete pvc rapidast-pvc
  (( counter++ ))
done

python find_alert_types.py

if [ $phase != "Succeeded" ]; then
    echo "Pod $rapidast_pod failed. Look at pod logs in archives (results/*/pod_logs.out)"
    exit 1
fi
