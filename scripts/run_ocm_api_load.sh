#!/bin/bash

# declare tests with rate and duration. Duration will be in minutes
# create_cluster, create-services, get-services and patch-services skipped till they get fixed and stabilized
export tests="
self-access-token 5/s 5 \n
list-subscriptions 5/s 5 \n
access-review 50/s 5 \n
register-new-cluster 2/s 5 \n
register-existing-cluster 50/s 5 \n
list-clusters 20/s 5 \n
get-current-account 10/s 5 \n
quota-cost 10/s 5 \n
resource-review 5/s 5 \n
self-terms-review 15/s 5 \n
certificates 10/s 5 \n
cluster-authorizations 1/s 5 linear 6 20 1"

create_aws_key(){
    # Delete aws keys if more than 1 key exists
    arr=(`aws iam list-access-keys --user-name OsdCcsAdmin --output text --query 'AccessKeyMetadata[*].AccessKeyId'`)
    arraylength=${#arr[@]}
    if [[ $arraylength -ge 1 ]]; then
        unset arr[$arraylength-1]
    fi
    for i in ${!arr[@]}
    do
        aws iam delete-access-key --user-name OsdCcsAdmin --access-key-id ${arr[i]}
    done

    echo "Creating aws key with admin user for OCM testing"
    admin_key=$(aws iam create-access-key --user-name OsdCcsAdmin --output json)
    export AWS_OSDCCADMIN_KEY=$(echo $admin_key | jq -r '.AccessKey.AccessKeyId')
    export AWS_OSDCCADMIN_SECRET=$(echo $admin_key | jq -r '.AccessKey.SecretAccessKey')
    sleep 60
}


run_ocm_api_load(){
    BASEDIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
    echo "Base directory $BASEDIR"

    # export environment variables shared by airflow (avoid overriding local env vars)
    rm -rf $BASEDIR/local_env.txt
    env > $BASEDIR/local_env.txt
    while IFS="=" read -r key value; do
        if ! grep -q "$key=" $BASEDIR/local_env.txt; then
            if [[ ! $key == *"."* ]]; then
                export $key="${value}" || true
            fi
        fi
    done < $BASEDIR/environment.txt

    export ES_SERVER="https://$ES_SERVER_USER:$ES_SERVER_PASS@$ES_SERVER_URL"

    echo "# Benchmark UUID: ${UUID}"

    echo " Clone and build the binary"
    git clone https://github.com/cloud-bulldozer/ocm-api-load $BASEDIR/ocm-api-load
    export TESTDIR=$BASEDIR/ocm-api-load
    echo "Test directory $TESTDIR"
    cd $TESTDIR
    go mod download
    make

    create_aws_key

    # Run each test individually
    start_time=$(date +%s)
    echo -e $tests | while read -a var; do
        tname=""
        trate=""
        tduration=0
        rampoptions=""

        if [ ${#var[@]} -eq 3 ]; then
            tname=${var[0]}
            trate=${var[1]}
            tduration=${var[2]}
        else
            tname=${var[0]}
            trate=${var[1]}
            tduration=${var[2]}
            IFS='/' read -r srate unit <<<"$trate"
            rampoptions="--ramp-type ${var[3]} --ramp-steps ${var[4]} --end-rate ${var[5]} --start-rate $srate --ramp-duration ${var[6]}"
        fi

        # As each test runs for a longer duration, aws OsdCcsAdmin key migt have been deleted if rosa cluster is created in parallel
        aws_osdccadmin_keys=`aws iam list-access-keys --user-name OsdCcsAdmin --output text --query 'AccessKeyMetadata[*].AccessKeyId'`
        if [[ "$aws_osdccadmin_keys" != *"$AWS_OSDCCADMIN_KEY"* ]]; then
            echo "create AWS OsdCcsAdmin key as it got deleted..."
            create_aws_key
        fi
        echo $GATEWAY_URL
	# Timeout runs ocm-load-test for the specified duration even if airflow killed this script (when user wants to stop benchmark execution). This helps in ocm-load-test to cleanup resources it created. 10 minutes extra timeout is set so that test can prepare results after running for the given duration.
	# kill-after option needs sudo permissions
        timeout --kill-after=60s --preserve-status $(((tduration + 20) * 60)) $TESTDIR/build/ocm-load-test --aws-region $AWS_DEFAULT_REGION --aws-account-id $AWS_ACCOUNT_ID --aws-access-key $AWS_OSDCCADMIN_KEY --aws-access-secret $AWS_OSDCCADMIN_SECRET --cooldown $COOLDOWN --duration $tduration --elastic-index ocm-load-metrics --elastic-insecure-skip-verify=true --elastic-server $ES_SERVER --gateway-url $GATEWAY_URL --client-id $OCM_CLIENT_ID --client-secret $OCM_CLIENT_SECRET --ocm-token-url $OCM_TOKEN_URL --output-path $TESTDIR/results --rate $trate --test-id $UUID --test-names $tname $rampoptions || true
	sleep $COOLDOWN
    done
    benchmark_rv=$?
    end_time=$(date +%s)

    # scraping metrics
    export KUBE_ES_INDEX=ocm-uhc-acct-mngr
    envsubst < $TESTDIR/ci/templates/kube-burner-config.yaml > $TESTDIR/kube-burner-am-config.yaml
    export KUBE_ES_INDEX=ocm-uhc-clusters-service
    envsubst < $TESTDIR/ci/templates/kube-burner-config.yaml > $TESTDIR/kube-burner-cs-config.yaml
    curl -LsS ${KUBE_BURNER_RELEASE_URL} | tar xz --directory=$TESTDIR/
    echo "Running kube-burner index to scrap metrics from UHC account manager service from ${start_time} to ${end_time} and push to ES"
    $TESTDIR/kube-burner index -c $TESTDIR/kube-burner-am-config.yaml --uuid=${UUID} -u=${PROM_URL} --job-name ocm-api-load --token=${PROM_TOKEN} -m=$TESTDIR/ci/templates/metrics_acct_mgmr.yaml --start $start_time --end $end_time
    echo "UHC account manager Metrics stored at elasticsearch server "$ES_SERVER" on index $KUBE_ES_INDEX with UUID $UUID and jobName: ocm-api-load"

    echo "Running kube-burner index to scrap metrics from UHC clusters service from ${start_time} to ${end_time} and push to ES"
    export KUBE_ES_INDEX=ocm-uhc-clusters-service
    $TESTDIR/kube-burner index -c $TESTDIR/kube-burner-cs-config.yaml --uuid=${UUID} -u=${PROM_URL} --job-name ocm-api-load --token=${PROM_TOKEN} -m=$TESTDIR/ci/templates/metrics_clusters_service.yaml --start $start_time --end $end_time
    echo "UHC clusters service metrics stored at elasticsearch server "$ES_SERVER" on index $KUBE_ES_INDEX with UUID $UUID and jobName: ocm-api-load"

    echo "converting start and end times into milliseconds for creating Result URLs"
    start_time=`expr $start_time \* 1000`
    end_time=`expr $end_time \* 1000`

    echo "Results URLs"
    echo "Account Manager Dashboard $GRAFANA_URL/d/uhc-account-manager/uhc-account-manager?orgId=1&var-uuid=${UUID}&var-datasource=ocm-uhc-acct-mngr&from=$start_time&to=$end_time"
    echo "Clusters Service Dashboard $GRAFANA_URL/d/uhc-clusters-service/uhc-clusters-service?orgId=1&var-datasource=ocm-uhc-clusters-service&var-uuid=${UUID}&from=$start_time&to=$end_time"

    # echo $UUID at the end is needed to pass UUID to cleanup task
    echo $UUID
    exit $benchmark_rv
}

run_ocm_api_load
