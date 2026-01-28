# NetObserv Performance Scripts
The purpose of the scripts in this directory is to measure [netobserv](https://github.com/netobserv/network-observability-operator) metrics performance.

Multiple workloads are run to generate traffic for the cluster:
1. [node-density-heavy](https://polarion.engineering.redhat.com/polarion/#/project/OSE/workitem?id=OCP-56616)
2. [ingress-perf](https://polarion.engineering.redhat.com/polarion/#/project/OSE/workitem?id=OCP-70716)
3. [cluster-density-v2](https://polarion.engineering.redhat.com/polarion/#/project/OSE/workitem?id=OCP-56617)

Note that [ingress-perf](https://polarion.engineering.redhat.com/polarion/#/project/OSE/workitem?id=OCP-70716) replaced the [router-perf](https://polarion.engineering.redhat.com/polarion/#/project/OSE/workitem?id=OCP-56618) test case we used for 1.5 and below

## Prerequisites
1. Create an OCP4 cluster
2. Set your `kubeconfig` and login to your cluster as `kubeadmin` - you can verify that you are successfully connected to the cluster by running the simple check below:
```bash
$ oc whoami
kube:admin
```
3. Depending on which functions within `netobserv.sh` you plan to use, you may also need to install the AWS CLI and properly set your credentials
4. If you're doing an installation, make sure you set the following env variables
```bash
$ export INSTALLATION_SOURCE # Should be 'Official', 'Internal', 'OperatorHub' or 'Source'
$ export UPSTREAM_IMAGE      # only needed if deploying 'Source' and testing a premerge image
$ export DOWNSTREAM_IMAGE    # only needed if deploying 'Internal' NetObserv Operator OR 'Unreleased' Loki Operator
$ export MAJOR_VERSION       # only needed if deploying 'Internal' and using aosqe-index image
$ export MINOR_VERSION       # only needed if deploying 'Internal' and using aosqe-index image
$ export LOKI_OPERATOR       # will use 'Released' if not set otherwise
$ export LOKISTACK_SIZE      # will use '1x.extra-small' if not set otherwise
```

### Creating LokiStack using Loki Operator
It is recommended to use Loki Operator to create a LokiStack for Network Observability. To install Loki Operator and create a LokiStack, run `$ source netobserv.sh ; deploy_lokistack`. Ensure you set the `LOKI_OPERATOR` and `LOKISTACK_SIZE` environmental variables to your desired values first - otherwise `Released` and `1x.extra-small` will be used, respectively.

To create LokiStack manually, the following steps can be performed:
1. Create a Loki Operator subscription with `$ oc apply -f loki/loki-<version>-subscription.yaml` to install Loki Operator. Loki Operator controller pod should be running in `openshift-operators-redhat` namespace.
2. Create an AWS secret for S3 bucket to be used for LokiStack using the `$ ./deploy-loki-aws-secret.sh` script. By default, it is setup to use `netobserv-ocpqe-default` S3 bucket.
3. Multiple sizes of LokiStack are supported and configs are added here. Depending upon the LokiStack size, high-end machine types might be required for the cluster:
    * lokistack-1x-exsmall.yaml - Extra-small t-shirt size LokiStack.
        - Requirements: Can be run on `t2.micro` machines.
        - Use case: For demos, development and feature testing. Should NOT be used for testing.
    * lokistack-1x-small.yaml - Small t-shirt size LokiStack
        - Requirements: `m6i.4xlarge` machines.
        - Use case: Standard performance/scale testing.
    * lokistack-1x-medium.yaml - Medium t-shirt size LokiStack
        - Requirements: `m6i.8xlarge` machines.
        - Use case: Large-scale performance/scale testing.
    Depending upon your cluster size and use case, run `$ oc apply -f <lokistack yaml manifest>`
4. LokiStack should be created under `netobserv` namespace

### Installing the Network Observability Operator
There are four sources from which you can install the operator which are detailed in the below sections. The installation source is determined by the value of the `INSTALLATION_SOURCE` env variable. Once this and the other nessessary variables are set, you can proceed with the installation by navigating to the `scripts/` directory and running `$ source netobserv.sh ; deploy_netobserv`

#### Official
The latest officially-released version of the downstream operator. It is hosted on the [Red Hat Catalog](https://catalog.redhat.com/software/containers/network-observability/network-observability-operator-bundle) and is the productized version of the operator available to Red Hat customers.

#### Internal
Continuous internal bundles are created via the Konflux build system

#### OperatorHub
The latest officially-released version of the upstream operator. It is hosted on [OperatorHub](https://operatorhub.io/operator/netobserv-operator) and is the community version of the operator available to all.

#### Source
GitHub Actions is used to [build and push images from the upstream operator repository](https://github.com/netobserv/network-observability-operator/actions) to [quay.io](https://quay.io/repository/netobserv/network-observability-operator-catalog?tab=tags) where the `main` tag is used to track the Github `main` branch.

#### Pre-merge images
If you want to install a premerge operator image that is present on quay.io instead of the `main` image, you can do so by setting the `$OPERATOR_PREMERGE_OVERRIDE` variable to the SHA hash of the premerge image, e.g. `e2bdef6` - note please select source installation method for using pre-merge images of operator
If you want to install the operator with pre-merge component images instead of the operator defined images, you can do so by setting the `$EBPF_PREMERGE_OVERRIDE`, `$FLP_PREMERGE_OVERRIDE`, `$PLUGIN_PREMERGE_OVERRIDE` variables for EBPF, FLP, Plugin respectively to the SHA hash of the premerge image, e.g. `e2bdef6`

### Updating common parameters of flowcollector
Initial configuration of flowcollector is set via the CRD, in the case of this repo that lies under `scripts/netobserv/flows_v1beta2_flowcollector.yaml`

You can update common parameters of flowcollector individually with the following commands:
- **eBPF Sampling rate:** `$ oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/agent/ebpf/sampling", "value": <value>}]"`
- **eBPF Memory limit:** `$ oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/agent/ebpf/resources/limits/memory", "value": "<value>Mi"}] -n netobserv`
- **FLP CPU limit:** `$ oc patch flowcollector  cluster --type=json -p "[{"op": "replace", "path": "/spec/flowlogsPipeline/resources/limits/cpu", "value": "<value>m"}]"`
    -  Note that 1000m = 1000 millicores, i.e. 1 core
- **FLP Memory limit:**: `$ oc patch flowcollector  cluster --type=json -p "[{"op": "replace", "path": "/spec/flowlogsPipeline/resources/limits/memory", "value": "<value>Mi"}]"`
- **FLP Replicas:** `$ oc patch flowcollector  cluster --type=json -p "[{"op": "replace", "path": "/spec/flowlogsPipeline/replicas", "value": <value>}]"`

### Install Kafka
To install Kafka, run `$ source netobserv.sh ; deploy_kafka`. Ensure you set `TOPIC_PARTITIONS` and `FLP_KAFKA_REPLICAS` environmental variables to your desired values first - otherwise values of `6` and `3` will be used, respectively.

### Dittybopper
Dittybopper allows for live viewing of the following metrics:
* Flows processed per minute
* Flows processed/written/dropped per second
* Node traffic received per second
* Ingress Bytes processed per second
* CPU usage of eBPF, FLP, Kafka, Loki, and the NetObserv Controller and Console Plugin
* Memory (RSS) usage of eBPF, FLP, Kafka, Loki, and the NetObserv Controller and Console Plugin
* Kafka and Loki PVC usage
* Loki Data Rate

To install Dittybopper, follow the steps below:
1. Clone the [performance-dashboards](https://github.com/cloud-bulldozer/performance-dashboards) repo if you haven't already
2. From `performance-dashboards/dittybopper`, run `$ ./deploy.sh -i $WORKSPACE/ocp-qe-perfscale-ci/scripts/queries/netobserv_dittybopper.json`
3. If the data isn't visible, you can manually import it by going to the Grafana URL (can be obtained with `$ oc get routes -n dittybopper`), logging in as `admin`, and uploading the relevant dittybopper config file in the `Dashboards` view.

## Testing with PerfScale CI
While node-density-heavy and cluster-density-v2 workload scenarios are run nightly and weekly respectively, to debug in a live cluster, pull request can be created against [openshift/release](https://github.com/openshift/release) repo to run rehearsals for the PerfScale tests, [example PR](https://github.com/openshift/release/pull/73503)

## Network Observability Prometheus and Elasticsearch tool (NOPE)
The Network Observability Prometheus and Elasticsearch tool, or NOPE, is a Python program that is used for collecting and sharing performance data for a given OpenShift cluster running the Network Observability Operator, using Prometheus range queries for collection and Elasticsearch servers for storage. It also has run modes for uploading local JSON files to Elasticsearch as well as setting and fetching baselines for given workloads.

### Prerequisties
1. Ensure you have Python 3.9+ and Pip installed (verify with `python --version` and `pip --version`)
2. Install requirements with `pip install -r scripts/requirements.txt`
3. If you wish to upload to Elasticsearch, set the following environmental variables:
```bash
export ES_USERNAME=<elasticsearch username>
export ES_PASSWORD=<elasticsearch password>
export ES_SERVER=https://search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com
```
4. Run the tool with `./scripts/nope.py`

To see all command line options available for the NOPE tool, you can run it with the `--help` argument.

### Standard Mode
Prometheus queries are sourced from the `netobserv_prometheus_queries.yaml` file within the `scripts/queries/` directory by default - check out that file to see what data the NOPE tool is collecting. Note this can be overriden with the `--yaml-file` flag to run other queries from within other files.

A raw JSON file will be written to the `data/` directory in the project - note this directory will be created automatically if it does not already exist. You can also explictily disable Elasticsearch uploading with the `--dump-only` flag.

### Upload Mode
Data that has been dumped to a JSON file, either due to an issue with Elasticsearch or done explicitly, can be uploaded to Elasticsearch later using the NOPE tool's Upload mode. Note that the specified JSON file must be in the `data/` directory. Also, you do not need to be connected to an OpenShift cluster if you are running in Upload mode.

### Baseline Mode
The NOPE tool can also be used for fetching and uploading baselines on a workload-by-workload basis by running it in Baseline mode. Fetching is based on workloads and ISO timestamps - for a given workload, the NOPE tool will fetch the latest baseline present on the specified Elasticsearch server and dump the UUID of that baseline to a `baseline.json` file in the `data/` directory. Uploading is based on UUID - the NOPE tool will gather data about the test run on the specified UUID and create a new baseline document in Elasticsearch. Note you do not need to be connected to an OpenShift cluster if you are running in Baseline mode.

## Change point detection and comparison with Orion:
[Orion](https://github.com/cloud-bulldozer/orion/?tab=readme-ov-file#orion---cli-tool-to-find-regressions) is a tool aimed to detect the change point in the performance metrics across several past runs.

To detech regressions and change point use `--hunter-analyze` algorithm and to compare 2 uuids, use `--cmr` algorithm, below are the example commands of both runs:

## Compare 2 uuids with Orion:

```bash
export workers=25
export es_metadata_index=ospst-perf-scale-ci*
export es_benchmark_index=ospst-prod-netobserv-datapoints*
export version=4.20.0
export ES_SERVER=https://$ES_USERNAME:$ES_PASSWORD@opensearch.app.intlab.redhat.com
orion cmd --config scripts/queries/netobserv-orion-node-density-heavy-ospst.yaml --uuid 4edb6734-f080-43f6-82ca-05b23e294d87 --baseline a2ff22ab-63cb-4aa2-a253-e9aaadc115a9 --cmr
```

## Detect a change point:
```bash
export workers=25
export es_metadata_index=perf_scale_ci*
export es_benchmark_index=prod-netobserv-datapoints*
export version=4.20.0
export ES_SERVER=https://$ES_USERNAME:$ES_PASSWORD@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com
orion --config scripts/queries/netobserv-orion-node-density-heavy.yaml --hunter-analyze --lookback 15d
```

Note that orion config files with suffix `*-ospst.yaml` are custom to OpenSearch instance: https://opensearch-dashboard.app.intlab.redhat.com (VPN Required), credentials can be obtained from bitwarden.

Orion config files without `*-ospst.yaml` are for OpenSearch instance https://search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com/ , data here is only preserved for last 60 days and older data can be found on https://opensearch-dashboard.app.intlab.redhat.com
