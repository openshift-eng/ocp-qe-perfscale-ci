#!/bin/bash
set -o nounset
set -o errexit
set -o pipefail

function run_command() {
    local CMD="$1"
    echo "Running Command: ${CMD}"
    eval "${CMD}"
}

function cli_Login() {
    # set the parameters we'll need as env vars
    AZURE_AUTH_LOCATION=$OCP_AZURE
    AZURE_AUTH_CLIENT_ID="$(cat ${AZURE_AUTH_LOCATION} | jq -r .clientId)"
    AZURE_AUTH_CLIENT_SECRET="$(cat ${AZURE_AUTH_LOCATION} | jq -r .clientSecret)"
    AZURE_AUTH_TENANT_ID="$(cat ${AZURE_AUTH_LOCATION} | jq -r .tenantId)"
    # az should already be there
    command -v az
    az version
    echo "$(date -u --rfc-3339=seconds) - Logging in to Azure..."
    az login --service-principal -u "${AZURE_AUTH_CLIENT_ID}" -p "${AZURE_AUTH_CLIENT_SECRET}" --tenant "${AZURE_AUTH_TENANT_ID}" --output none
    az account set --subscription `cat $AZURE_AUTH_LOCATION | jq -r '.subscriptionId'`
}

function getResourceGroup() {
    machine_api=$( oc get machinesets --no-headers -A -o name | head -n1)
    RESOURCE_GROUP=$(oc get $machine_api -o yaml -n openshift-machine-api  | yq .spec.template.spec.providerSpec.value.networkResourceGroup)

    export RESOURCE_GROUP
}


function getResourceGroup2() {
    machine_api=$( oc get machinesets --no-headers -A -o name | head -n1)
    RESOURCE_GROUP=$(oc get $machine_api -o yaml -n openshift-machine-api  | yq .spec.template.spec.providerSpec.value.resourceGroup | tr -d '"')

}
cli_Login

OUTBOUND_PORTS=${OUTBOUND_PORTS:="64"}
OUTBOUND_RULE_NAME=${OutboundNATAllProtocols:="OutboundNATAllProtocols"}

getResourceGroup

 
LOAD_BALACER="$(az network lb list -g $RESOURCE_GROUP | jq -r '.[].name' | grep -v internal)"

if [[ -z $LOAD_BALACER ]]; then 

    getResourceGroup2
fi 

echo "Check outbound port"
az network lb outbound-rule list -g $RESOURCE_GROUP -o table --lb-name $LOAD_BALACER
echo "Updating outbound port"
az network lb outbound-rule update -g $RESOURCE_GROUP --lb $LOAD_BALACER --outbound-ports $OUTBOUND_PORTS --name $OUTBOUND_RULE_NAME
echo "Check outbound port after update"
az network lb outbound-rule list -g $RESOURCE_GROUP -o table --lb-name $LOAD_BALACER