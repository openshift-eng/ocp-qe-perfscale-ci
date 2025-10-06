#!/usr/bin/env bash

LOKI_BUCKET_NAME=${1:-netobserv-ocpqe-default}
NAMESPACE=${2:-netobserv-loki}
SECRETNAME="s3-secret"
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-2}
ENDPOINT="https://s3.${AWS_DEFAULT_REGION}.amazonaws.com"
AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}"
AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}"

set_credentials_from_local() {
    AWS_ACCESS_KEY_ID="$(aws configure get aws_access_key_id)"
    AWS_SECRET_ACCESS_KEY="$(aws configure get aws_secret_access_key)"
    AWS_DEFAULT_REGION="$(aws configure get region)"
    ENDPOINT="https://s3.${AWS_DEFAULT_REGION}.amazonaws.com"
}

set_credentials_from_provider() {
    AWS_ACCESS_KEY_ID=$(oc get secret aws-creds -n kube-system -o json | jq -r '.data.aws_access_key_id' | base64 -d)
    AWS_SECRET_ACCESS_KEY=$(oc get secret aws-creds -n kube-system -o json | jq -r '.data.aws_secret_access_key' | base64 -d)
}

set_aws_credentials() {
    echo "CreateAWSSecret: get aws credentials"

    # use credentials in env as the first option
    # use credentials in local as the second option
    if [[ $AWS_ACCESS_KEY_ID == "" || ${AWS_SECRET_ACCESS_KEY} == "" ]]; then
        if aws configure get region; then
            echo "CreateAWSSecret: use credentials in local"
            set_credentials_from_local
        fi
    fi

    # use cloud provider as the third option
    if [[ $AWS_ACCESS_KEY_ID == "" || ${AWS_SECRET_ACCESS_KEY} == "" ]]; then
        if oc get secret aws-creds -n kube-system; then
            echo "CreateAWSSecret: try credentials in kube-system/aws-creds"
            set_credentials_from_provider
        fi
    fi

    if [[ $AWS_ACCESS_KEY_ID == "" || ${AWS_SECRET_ACCESS_KEY} == "" ]]; then
        echo "CreateAWSSecret: Error: option no value! AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"
        exit 1
    fi
}

# Create s3 bucket
create_s3_bucket() {
    if aws configure get region; then
        echo "bucket: Create s3 bucket $LOKI_BUCKET_NAME if it does not exist"
    else
        echo "bucket: Warning: Can not connect to aws, ensure bucket is ready before trying to deploy lokistack"
        return 0
    fi
    # todo: use query https://jmespath.org/
    # aws s3api list-buckets --query \'Buckets[?Name == \"${LOKI_BUCKET_NAME}\"].Name\'`
    aws s3api list-buckets | grep ${LOKI_BUCKET_NAME}
    if [[ $? == 0 ]]; then
        echo "bucket: deleting existing bucket"
        aws s3 rm s3://$LOKI_BUCKET_NAME --recursive
        sleep 30
        aws s3 rb s3://$LOKI_BUCKET_NAME --force
    fi
    aws s3api create-bucket --bucket $LOKI_BUCKET_NAME --region $AWS_DEFAULT_REGION --create-bucket-configuration LocationConstraint=$AWS_DEFAULT_REGION
    if [[ $? == 0 ]]; then
        echo "bucket: created new bucket $LOKI_BUCKET_NAME"
    else
        echo "bucket: Error: fail to create bucket $LOKI_BUCKET_NAME!"
        exit 1
    fi
}

create_secret() {
    set_aws_credentials
    oc delete secret ${SECRETNAME} -n ${NAMESPACE} || :
    oc -n ${NAMESPACE} create secret generic ${SECRETNAME} \
        --from-literal=endpoint="${ENDPOINT}" \
        --from-literal=region="${AWS_DEFAULT_REGION}" \
        --from-literal=bucketnames="${LOKI_BUCKET_NAME}" \
        --from-literal=access_key_id="${AWS_ACCESS_KEY_ID}" \
        --from-literal=access_key_secret="${AWS_SECRET_ACCESS_KEY}"
    if [[ $? == 0 ]]; then
        echo "CreateAWSSecret: Secret created, region=${AWS_DEFAULT_REGION} bucket=${LOKI_BUCKET_NAME}"
    fi
}

main() {
    create_secret
    create_s3_bucket
}

main
