#!/usr/bin/env python3

import os
import sys
import json
import yaml
import uuid
import time
import urllib3
import pathlib
import jenkins
import logging
import argparse
import requests
from datetime import datetime, timezone
import subprocess
import coloredlogs
from elasticsearch import Elasticsearch


# disable SSL and warnings
os.environ["PYTHONHTTPSVERIFY"] = "0"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# directory constants
ROOT_DIR = str(pathlib.Path(__file__).parent.parent)
SCRIPT_DIR = ROOT_DIR + "/scripts"
DATA_DIR = ROOT_DIR + "/data"

# NOPE constants
THANOS_URL = ""
TOKEN = ""
YAML_FILE = ""
QUERIES = None
RESULTS = {"prometheus_data": []}
DEBUG = False
JIRA = None

# prometheus query constants
START_TIME = None
END_TIME = None
STEP = None

# jenkins env constants
JENKINS_URL = "https://jenkins-csb-openshift-qe-mastern.dno.corp.redhat.com/"
JENKINS_JOB = None
JENKINS_BUILD = None
JENKINS_SERVER = None
NOO_BUNDLE_VERSION = None
UUID = None
SUPPORTED_WORKLOADS = [
    "node-density-heavy",
    "ingress-perf",
    "cluster-density-v2",
]

# elasticsearch constants
ES_URL = "search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"
ES_USERNAME = os.getenv("ES_USERNAME")
ES_PASSWORD = os.getenv("ES_PASSWORD")
DUMP_ONLY = False
UPLOAD_FILE = None
BASELINE_TO_FETCH = None
BASELINE_TO_UPLOAD = None
JENKINS_BUILD_URL = None
UUID_REPLACEMENT_STR = None

# default prom. retention is 15d
PROM_RETENTION_SECONDS = 15 * 24 * 60 * 60
# assumption is avg chunk size (1.77) * retention (15*24*60*60)
# Source: https://tanmay-bhat.github.io/posts/how-to-calculate-the-storage-space-required-for-prometheus-server/
PROM_CHUNK_SIZE_STORAGE_BYTES = 1.77 * PROM_RETENTION_SECONDS


def get_iso_timestamp(unix_timestamp):
    """takes in a unix timestamp and returns an iso timestamp representation
    iso timestamp will be Elasticsearch compatible
    """
    return datetime.utcfromtimestamp(int(unix_timestamp)).isoformat() + "Z"


def get_epoch_from_iso(isotime):
    """
    Takes ISO timestamp in format '%Y-%m-%dT%H:%M:%SZ' and returns epoch seconds
    """
    utc_dt = datetime.strptime(isotime, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    timestamp = (
        utc_dt - datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    ).total_seconds()
    return int(timestamp)


def process_query(uuid, metric_name, query, raw_data):
    """takes in a UUID, Prometheus metric name, query and its successful execution result
    reformats data into format desired for Elasticsearch upload
    returns dict object with post-processed data
    """

    # intialize post-processing data object
    clean_data = []

    # capture metadata and value artifacts from prometheus return object
    try:
        for result in raw_data["data"]["result"]:
            for data_point in result["values"]:
                metadata = result["metric"]
                metadata["query"] = query
                iso_timestamp = get_iso_timestamp(data_point[0])
                clean_data.append(
                    {
                        "uuid": uuid,
                        "metric_name": metric_name,
                        "data_type": "datapoint",
                        "iso_timestamp": iso_timestamp,
                        "unix_timestamp": data_point[0],
                        "value": float(data_point[1]),
                        "metadata": metadata,
                    }
                )

    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.error(f"Error cleaning {metric_name} data from query {query}: {e}")
        logging.error(f"raw_data: {raw_data}")
        logging.error(
            f"Dumping partially-cleaned data to {DATA_DIR}/partial_data_{timestamp}.json"
        )
        dump_data_locally(timestamp, partial=True)
        sys.exit(1)

    # return cleaned data
    return clean_data


def run_query(metric_name, query, start_time, end_time):
    """takes in a Prometheus query
    executes a range query based on global constants
    returns the JSON data delivered by Prometheus or an exception if the query fails
    """

    # construct request
    headers = {"Authorization": f"Bearer {TOKEN}"}
    endpoint = f"{THANOS_URL}/api/v1/query_range"
    params = {"query": query, "start": start_time, "end": end_time, "step": STEP}

    # make request and return data
    data = requests.get(endpoint, headers=headers, params=params, verify=False)
    if data.status_code != 200:
        raise Exception(
            f"metricName '{metric_name}' with query '{query}'to fetch Prometheus data failed due to: {data.status_code} {data.reason}"
        )
    return data.json()


def run_commands(commands, outputs={}):
    """executes dictionary of commands where key is identifier and value is command
    raises Exception if command fails
    returns outputs dictionary, either new or appended to passed dict
    """

    # iterate through commands dictionary
    for command in commands:
        logging.debug(f"Executing command '{commands[command]}' to get {command} data")
        try:
            # execute next command in iteration
            result = subprocess.run(
                commands[command],
                capture_output=True,
                text=True,
                shell=True,
                timeout=600,
            )

            # record command stdout if execution was succesful
            output = result.stdout.strip()
            logging.debug(f"Got back result: {output}")

            # if aws_s3_bucket_usage command, split up the data to two different metadata fields
            if command == "aws_s3_bucket_usage":
                aws_data = output.replace(" ", "").splitlines()
                aws_buckets = aws_data[0].split(":", 1)[1]
                aws_size = aws_data[1].split(":", 1)[1]
                logging.debug(f"aws_s3_bucket_objects calculated as {aws_buckets}")
                outputs["aws_s3_bucket_objects"] = aws_buckets
                logging.debug(f"aws_s3_bucket_size calculated as {aws_size}")
                outputs["aws_s3_bucket_size"] = aws_size

            # otherwise map command output to dict entry
            else:
                outputs[command] = output

        except Exception as e:
            # if command failed but was AWS-specific, don't block, just continue
            if "aws" in command:
                output = result.stderr
                logging.error(
                    f"Got back result: {output} from AWS command - skipping..."
                )
                outputs[command] = "N/A"

            # otherwise, log the error and exit
            else:
                logging.error(
                    f"Command '{command}' execution resulted in stderr output: {e}"
                )
                sys.exit(1)

    # if all commands were successful return outputs dictionary
    return outputs


def get_netobserv_env_info():
    """gathers information about netobserv operator env
    returns info dictionary where key is identifier and value is command output
    """

    # intialize info and base_commands objects
    iso_timestamp = get_iso_timestamp(START_TIME)
    info = {
        "uuid": UUID,
        "jira": JIRA,
        "metric_name": "netobservEnv",
        "data_type": "metadata",
        "iso_timestamp": iso_timestamp,
        "noo_bundle_version": NOO_BUNDLE_VERSION,
        "uuid_replaced_info": UUID_REPLACEMENT_STR,
    }
    base_commands = {
        "ocp": 'oc get co/authentication -o=jsonpath="{.status.versions[0].version}"',
        "release": 'oc get pods -l app=netobserv-operator -o jsonpath="{.items[*].spec.containers[1].env[0].value}" -A',
        "arch": 'oc get node -o jsonpath="{.items[0].status.nodeInfo.architecture}"',
        "loki": 'oc get sub -n openshift-operators-redhat loki-operator -o jsonpath="{.status.currentCSV}"',
        "deploymentModel": 'oc get flowcollector -o jsonpath="{.items[*].spec.deploymentModel}" -n netobserv',
        "agent": 'oc get flowcollector -o jsonpath="{.items[*].spec.agent.type}"',
        "aws_s3_bucket_name": "oc extract cm/lokistack-config -n netobserv --keys=config.yaml --confirm --to=/tmp | xargs -I {} egrep bucketnames {} | cut -d: -f 2 | xargs echo -n",
    }

    # collect data from cluster about netobserv operator and store in info dict
    info = run_commands(base_commands, info)

    # get flp_kind data from kafka data
    deploymentModel = info["deploymentModel"].lower()
    logging.debug(f"Found deployment model {deploymentModel}")
    if deploymentModel == "kafka":
        logging.debug("Kafka is enabled - flp_kind is 'Deployment'")
        info["flp_kind"] = "Deployment"
    else:
        logging.debug("Kafka is disabled - flp_kind is 'DaemonSet'")
        info["flp_kind"] = "DaemonSet"

    # run any additional commands needed and append data to info dictionary
    agent = info["agent"].lower()
    logging.debug(f"Found collector agent {agent}")
    s3_bucket_name = info["aws_s3_bucket_name"]
    logging.debug(f"Found AWS S3 bucket name {s3_bucket_name}")

    # noo_start_time could have multiple start time values if subscribed to operator more than once
    additional_commands = {
        "sampling": f'oc get flowcollector -o jsonpath="{{.items[*].spec.agent.{agent}.sampling}}"',
        "cache_active_time": f'oc get flowcollector -o jsonpath="{{.items[*].spec.agent.{agent}.cacheActiveTimeout}}"',
        "cache_max_flows": f'oc get flowcollector -o jsonpath="{{.items[*].spec.agent.{agent}.cacheMaxFlows}}"',
        "aws_s3_bucket_usage": f"aws s3 ls --summarize --human-readable --recursive s3://{s3_bucket_name} | tail -2",
        "noo_start_time": "oc get csv/"
        + info["release"]
        + " -o jsonpath='{.status.conditions[?(@.phase==\"Succeeded\")].lastUpdateTime}' -n openshift-netobserv-operator"
        + " | awk '{print $NF}'",
    }
    if deploymentModel == "kafka":
        additional_commands["kafka_replicas"] = (
            f'oc get flowcollector -o jsonpath="{{.items[*].spec.processor.kafkaConsumerReplicas}}"'
        )
        additional_commands["kafka_brokers"] = (
            f'oc get Kafka -o jsonpath="{{.items[*].spec.kafka.replicas}}" -n netobserv'
        )
    else:
        info["kafka_replicas"] = "N/A"
        info["kafka_brokers"] = "N/A"
    info = run_commands(additional_commands, info)

    # return all collected data
    return info


def get_jenkins_env_info():
    """gathers information about Jenkins env
    if build parameter data cannot be collected, only command line data will be included
    """

    # intialize info object
    iso_timestamp = get_iso_timestamp(START_TIME)
    info = {
        "uuid": UUID,
        "metric_name": "jenkinsEnv",
        "data_type": "metadata",
        "iso_timestamp": iso_timestamp,
        "jenkins_job_name": JENKINS_JOB,
        "jenkins_build_num": JENKINS_BUILD,
        "buildUrl": JENKINS_BUILD_URL,
    }

    # collect data from Jenkins server
    try:
        build_info = JENKINS_SERVER.get_build_info(JENKINS_JOB, JENKINS_BUILD)
        logging.debug(f"Jenkins Build Info: {build_info}")
        build_actions = build_info["actions"]
        build_parameters = None
        for action in build_actions:
            if action.get("_class") == "hudson.model.ParametersAction":
                build_parameters = action["parameters"]
                break
        if build_parameters is None:
            raise Exception("No build parameters could be found.")
        for param in build_parameters:
            del param["_class"]
            if param.get("name") == "VARIABLE":
                info["variable"] = int(param.get("value"))
            if param.get("name") == "WORKLOAD":
                info["workload"] = str(param.get("value"))
        # if workload is not explicitly set in Jenkins such as with router-perf, take it from the job name
        if info.get("workload") is None:
            info["workload"] = JENKINS_JOB.split("/")[-1]
        # check if a valid workload has been parsed
        if info["workload"] not in SUPPORTED_WORKLOADS:
            raise Exception(
                f"{info['workload']} is not in the list of supported workloads: {SUPPORTED_WORKLOADS}"
            )

    except Exception as e:
        logging.error(f"Failed to collect Jenkins build parameter info: {e}")

    # return all collected data
    return info


def dump_data_locally(timestamp, partial=False):
    """writes captured data in RESULTS dictionary to a JSON file
    file is saved to 'data_{timestamp}.json' in DATA_DIR system path if data is complete
    file is saved to 'partial_data_{timestamp}.json' in DATA_DIR system path if data is incomplete
    """

    # ensure data directory exists (create if not)
    pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

    # write prometheus data to data directory
    if not partial:
        with open(DATA_DIR + f"/data_{timestamp}.json", "w") as data_file:
            json.dump(RESULTS, data_file)
    else:
        with open(DATA_DIR + f"/partial_data_{timestamp}.json", "w") as data_file:
            json.dump(RESULTS, data_file)

    # return if no issues
    return None


def format_data_for_upload():
    """formats the data in RESULTS into a de-normalized payload for elasticsearch
    returns a de-normalized list
    """
    uuid = None
    payload = []

    if "jenkins_env" in RESULTS:
        payload.append(RESULTS["jenkins_env"])
        uuid = RESULTS["jenkins_env"]["uuid"]
    if "netobserv_env" in RESULTS:
        payload.append(RESULTS["netobserv_env"])
        if uuid is None:
            uuid = RESULTS["netobserv_env"]["uuid"]
        else:
            assert (
                uuid == RESULTS["netobserv_env"]["uuid"]
            ), "UUIDs for jenkinsEnv and netobservEnv did not match, data may be malformed"
    if "prometheus_data" in RESULTS and len(RESULTS["prometheus_data"]) > 0:
        for item in RESULTS["prometheus_data"]:
            clean_data = process_query(
                uuid, item["metric_name"], item["query"], item["raw_data"]
            )
            payload.extend(clean_data)

    return payload


def upload_data_to_elasticsearch():
    """uploads captured data in RESULTS dictionary to Elasticsearch"""

    # create Elasticsearch object and attempt index
    es = Elasticsearch(
        [f"https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443"],
        timeout=30,
        max_retries=10,
        retry_on_timeout=True,
    )

    documents = format_data_for_upload()
    start = time.time()
    for item in documents:
        metric_name = item.get("metric_name")
        if metric_name == "netobservEnv":
            index = "prod-netobserv-operator-metadata"
        elif metric_name == "jenkinsEnv":
            index = "prod-netobserv-jenkins-metadata"
        else:
            index = "prod-netobserv-datapoints"
        logging.debug(f"Uploading item '{item}' to index '{index}' in Elasticsearch")
        response = es.index(index=index, body=item)
        logging.debug(f"Response back was {response}")
    end = time.time()
    elapsed_time = end - start

    # close Elasticsearch object and return elapsed time for upload if no issues
    es.close()
    return elapsed_time


def upload_baseline_to_elasticsearch(uuid):
    """uploads baseline data for a given UUID from Elasticsearch"""

    # create Elasticsearch object
    es = Elasticsearch(
        [f"https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443"],
        timeout=30,
        max_retries=10,
        retry_on_timeout=True,
    )

    # get netobserv release info from Elasticsearch based off UUID
    releaseRes = es.search(
        index="prod-netobserv-operator-metadata",
        body={"query": {"match": {"uuid.keyword": uuid}}},
    )
    logging.debug(f"Response back from release fetch attempt was {releaseRes}")

    # ensure exactly 1 result was captured, exit if not
    releaseResNumHits = len(releaseRes["hits"]["hits"])
    if releaseResNumHits != 1:
        logging.error(f"Got {releaseResNumHits} hits - should be '1'")
        sys.exit(1)

    # parse out release info from response object and log
    release = releaseRes["hits"]["hits"][0]["_source"]["release"]
    logging.info(f"Got {release} for release from test results for UUID {uuid}")

    # get workload info from Elasticsearch based off UUID
    workloadRes = es.search(
        index="prod-netobserv-jenkins-metadata",
        body={"query": {"match": {"uuid.keyword": uuid}}},
    )
    logging.debug(f"Response back from workload fetch attempt was {workloadRes}")

    # ensure exactly 1 result was captured, exit if not
    workloadResNumHits = len(workloadRes["hits"]["hits"])
    if workloadResNumHits != 1:
        logging.error(f"Got {workloadResNumHits} hits - should be '1'")
        sys.exit(1)

    # parse out workload info from response object and log
    # if workload is not explicitly set in jenkins data such as with legacy router-perf, take it from the job name
    try:
        workload = workloadRes["hits"]["hits"][0]["_source"]["workload"]
    except KeyError:
        job_name = workloadRes["hits"]["hits"][0]["_source"]["jenkins_job_name"]
        workload = job_name.split("/")[-1]
    logging.info(f"Got {workload} for workload from test results for UUID {uuid}")

    # assemble baseline document
    iso_timestamp = get_iso_timestamp(time.time())
    document = {
        "uuid": uuid,
        "data_type": "baseline",
        "iso_timestamp": iso_timestamp,
        "workload": workload,
        "release": release,
    }

    # upload new baseline to Elasticsearch
    logging.debug(
        f"Uploading baseline document '{document}' to index 'prod-netobserv-baselines' in Elasticsearch"
    )
    baselineUploadRes = es.index(index="prod-netobserv-baselines", body=document)
    logging.debug(f"Response back from upload attempt was {baselineUploadRes}")

    # close Elasticsearch object and return
    es.close()
    return None


def fetch_baseline_from_elasticsearch(workload):
    """fetches baseline data for a given workload from Elasticsearch"""

    # create Elasticsearch object
    es = Elasticsearch(
        [f"https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443"],
        timeout=30,
        max_retries=10,
        retry_on_timeout=True,
    )

    # fetch most recent baseline for given workload
    baselineRes = es.search(
        index="prod-netobserv-baselines",
        body={
            "query": {"match": {"workload.keyword": workload}},
            "sort": [{"iso_timestamp": {"order": "desc"}}],
            "size": 1,
        },
    )
    logging.debug(f"Response back from baseline fetch attempt was {baselineRes}")

    # ensure exactly 1 result was captured, exit if not
    baselineResNumHits = len(baselineRes["hits"]["hits"])
    if baselineResNumHits != 1:
        logging.error(f"Got {baselineResNumHits} hits - should be '1'")
        sys.exit(1)

    # parse out uuid from response object and log
    baseline_uuid = baselineRes["hits"]["hits"][0]["_source"]["uuid"]
    logging.info(
        f"Got {baseline_uuid} for most recent baseline for workload {workload}"
    )

    # ensure data directory exists (create if not)
    pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

    # dump baseline to JSON so it can be consumed by other actors such as Jenkins
    with open(DATA_DIR + f"/baseline.json", "w") as baseline_file:
        json.dump({"BASELINE_UUID": baseline_uuid}, baseline_file)

    # close Elasticsearch object and return
    es.close()
    return None


def update_results_with_metrics_data(queries, start_time, end_time):
    # get prometheus data
    for entry in queries:
        metric_name = entry["metricName"]
        query = entry["query"]
        raw_data = run_query(metric_name, query, start_time, end_time)
        RESULTS["prometheus_data"].append(
            {"raw_data": raw_data, "query": query, "metric_name": metric_name}
        )


def get_prom_metrics_queries(noo_start_time):
    seconds_elapsed_since_noo_installed = int(END_TIME) - noo_start_time
    netobserv_prom_ratio = {
        "metricName": "NetObservPromSamplesRatio",
        "query": 'sum(scrape_samples_post_metric_relabeling{namespace=~"netobserv.*"}) / sum(scrape_samples_post_metric_relabeling)',
    }

    prom_cpu = {
        "metricName": "cpuPrometheusTotals",
        "query": f'sum(delta(pod:container_cpu_usage:sum{{namespace="openshift-monitoring", pod=~"prometheus-k8s.*"}}[{seconds_elapsed_since_noo_installed}s])) * (sum(scrape_samples_post_metric_relabeling{{namespace=~"netobserv.*"}}) / sum(scrape_samples_post_metric_relabeling))',
    }

    prom_rss = {
        "metricName": "rssPrometheusTotals",
        "query": f'sum(delta(container_memory_rss{{namespace="openshift-monitoring", pod=~"prometheus-k8s.*", container=""}}[{seconds_elapsed_since_noo_installed}s])) * (sum(scrape_samples_post_metric_relabeling{{namespace=~"netobserv.*"}}) / sum(scrape_samples_post_metric_relabeling))',
    }

    prom_netobserv_samples_size = {
        "metricName": "prometheusEstimatedStorageUsage",
        "query": f'sum(scrape_samples_post_metric_relabeling{{namespace=~"netobserv.*"}}) * {PROM_CHUNK_SIZE_STORAGE_BYTES}',
    }

    return [
        netobserv_prom_ratio,
        prom_cpu,
        prom_rss,
        prom_netobserv_samples_size,
    ]


def main():

    # get jenkins env data if applicable
    if JENKINS_SERVER is not None:
        RESULTS["jenkins_env"] = get_jenkins_env_info()

    # get netobserv env data
    RESULTS["netobserv_env"] = get_netobserv_env_info()

    noo_start_time_epoch = get_epoch_from_iso(
        RESULTS["netobserv_env"]["noo_start_time"]
    )

    # measure prometheus impact with start time as NOO pod start time
    prom_impact_queries = get_prom_metrics_queries(noo_start_time_epoch)
    update_results_with_metrics_data(
        prom_impact_queries, noo_start_time_epoch, END_TIME
    )

    # measure other metrics with start time as workload start time
    update_results_with_metrics_data(QUERIES, START_TIME, END_TIME)

    # log success if no issues
    logging.info(f"Data captured successfully")

    # either dump data locally or upload it to Elasticsearch
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    dump_data_locally(timestamp)
    logging.info(f"Data written to {DATA_DIR}/data_{timestamp}.json")
    if not DUMP_ONLY:
        try:
            elapsed_time = upload_data_to_elasticsearch()
            logging.info(f"Elasticsearch upload completed in {elapsed_time} seconds")
        except Exception as e:
            logging.error(
                f"Error uploading to Elasticsearch server: {e}\nA local dump to {DATA_DIR}/data_{timestamp}.json will be done instead"
            )
            dump_data_locally(timestamp)
            # using exit code of 2 here so that Jenkins pipeline can unqiuely identify this error
            sys.exit(2)

    # exit if no issues
    sys.exit(0)


if __name__ == "__main__":

    # initialize argument parser and mode subparsers
    parser = argparse.ArgumentParser(
        description="Network Observability Prometheus and Elasticsearch tool (NOPE)"
    )
    subparsers = parser.add_subparsers(dest="mode", help="Additional Run Modes")

    # set logging flags
    parser.add_argument(
        "--debug",
        default=False,
        action="store_true",
        help="Flag for additional debug messaging",
    )

    # set standard mode flags
    standard = parser.add_argument_group(
        "Standard Mode",
        "Connect to an OCP cluster and gather data via Prometheus queries",
    )
    standard.add_argument(
        "--yaml-file",
        type=str,
        default="netobserv_prometheus_queries.yaml",
        help='YAML file from which to source Prometheus queries - defaults to "netobserv_prometheus_queries.yaml"',
    )
    standard.add_argument("--starttime", type=str, help="Start time for range query")
    standard.add_argument("--endtime", type=str, help="End time for range query")
    standard.add_argument(
        "--step", type=str, default="60", help="Step time for range query"
    )
    standard.add_argument(
        "--jenkins-job", type=str, help="Jenkins job name to associate with run"
    )
    standard.add_argument(
        "--jenkins-build", type=str, help="Jenkins build number to associate with run"
    )
    standard.add_argument(
        "--uuid",
        type=str,
        help="UUID to associate with run - if none is provided one will be generated",
    )
    standard.add_argument(
        "--dump-only",
        default=False,
        action="store_true",
        help="Flag to dump data locally instead of uploading it to Elasticsearch",
    )
    standard.add_argument(
        "--jira",
        type=str,
        help='Jira ticket to associate with run - should be in the form of "NETOBSERV-123"',
    )
    standard.add_argument(
        "--noo-bundle-version",
        type=str,
        help="NOO Operator bundle associated with the run",
    )

    # set upload mode flags
    upload = subparsers.add_parser(
        "upload",
        description="Directly upload data from a previously generated JSON file to Elasticsearch",
        help="Directly upload data from a previously generated JSON file to Elasticsearch",
    )
    upload.add_argument(
        "--file",
        type=str,
        required=True,
        help='JSON file to upload to Elasticsearch. Must be in the "data" directory.',
    )

    # set baseline mode flags
    baseline = subparsers.add_parser(
        "baseline",
        description="Fetch an existing baseline from Elasticsearch or Upload a new baseline",
        help="Fetch an existing baseline from Elasticsearch or Upload a new baseline",
    )
    baseline_group = baseline.add_mutually_exclusive_group(required=True)
    baseline_group.add_argument(
        "--fetch", type=str, help="Fetch the most recent baseline for a given workload"
    )
    baseline_group.add_argument(
        "--upload", type=str, help="Upload a new baseline for a given UUID"
    )

    # parse arguments
    args = parser.parse_args()

    # set logging config
    DEBUG = args.debug
    if DEBUG:
        logging.basicConfig(level=logging.DEBUG)
        coloredlogs.install(level="DEBUG", isatty=True)
    else:
        logging.basicConfig(level=logging.INFO)
        coloredlogs.install(level="INFO", isatty=True)

    # if running in upload mode - immediately load JSON, upload, and exit
    if args.mode == "upload":
        UPLOAD_FILE = args.file
        upload_file_path = DATA_DIR + "/" + UPLOAD_FILE
        logging.info(
            f"Running NOPE tool in Upload mode - data from {upload_file_path} will be uploaded to Elasticsearch"
        )

        # read data json file
        with open(upload_file_path) as json_file:
            RESULTS = json.load(json_file)

        # upload data to elasticsearch
        try:
            elapsed_time = upload_data_to_elasticsearch()
            logging.info(f"Elasticsearch upload completed in {elapsed_time} seconds")
            sys.exit(0)
        except Exception as e:
            logging.error(f"Error uploading to Elasticsearch server: {e}")
            sys.exit(1)

    # if running in baseline mode - perform action based on argument and exit
    if args.mode == "baseline":
        BASELINE_TO_FETCH = args.fetch
        BASELINE_TO_UPLOAD = args.upload
        if BASELINE_TO_FETCH is not None:
            fetch_baseline_from_elasticsearch(BASELINE_TO_FETCH)
            sys.exit(0)
        else:
            upload_baseline_to_elasticsearch(BASELINE_TO_UPLOAD)
            sys.exit(0)

    # sanity check that kubeconfig is set
    result = subprocess.run(["oc", "whoami"], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(
            "Could not connect to cluster - ensure all the Prerequisite steps in the README were followed"
        )
        sys.exit(1)

    # log prometheus range query constants
    START_TIME = args.starttime
    END_TIME = args.endtime
    STEP = args.step
    if START_TIME == "" or END_TIME == "":
        logging.error("START_TIME and END_TIME are needed to proceed")
        sys.exit(1)
    else:
        logging.info(
            "Parsed Start Time: "
            + datetime.utcfromtimestamp(int(START_TIME)).strftime(
                "%I:%M%p%Z UTC on %m/%d/%Y"
            )
        )
        logging.info(
            "Parsed End Time:   "
            + datetime.utcfromtimestamp(int(END_TIME)).strftime(
                "%I:%M%p%Z UTC on %m/%d/%Y"
            )
        )
        logging.info("Step is:           " + STEP)

    # check if Jenkins arguments are valid and if so set constants
    raw_jenkins_job = args.jenkins_job
    raw_jenkins_build = args.jenkins_build
    if all(v is None for v in [raw_jenkins_job, raw_jenkins_build]):
        JENKINS_SERVER = None
    elif any(v is None for v in [raw_jenkins_job, raw_jenkins_build]):
        logging.error(
            "JENKINS_JOB and JENKINS_BUILD must all be used together or not at all"
        )
        sys.exit(1)
    else:
        JENKINS_JOB = raw_jenkins_job
        JENKINS_BUILD = int(raw_jenkins_build)
        logging.info(
            f"Associating run with Jenkins job {JENKINS_JOB} build number {JENKINS_BUILD}"
        )
        try:
            JENKINS_SERVER = jenkins.Jenkins(JENKINS_URL)
            version = JENKINS_SERVER.get_version()
        except Exception as e:
            logging.error("Error connecting to Jenkins server: ", e)
            sys.exit(1)

    NOO_BUNDLE_VERSION = args.noo_bundle_version
    if not NOO_BUNDLE_VERSION:
        logging.warn(
            "NOO_BUNDLE_VERSION is strongly recommended to set using --noo-bundle-version args"
        )
        NOO_BUNDLE_VERSION = "N/A"
        UUID_REPLACEMENT_STR = f"{get_iso_timestamp(START_TIME)}"
    else:
        UUID_REPLACEMENT_STR = f"{NOO_BUNDLE_VERSION}/{get_iso_timestamp(START_TIME)}"

    UUID_REPLACEMENT_STR += "/" + args.jira if args.jira else ""

    # determine UUID and Jira if applicable
    UUID = args.uuid
    if UUID is None:
        UUID = str(uuid.uuid4())
    logging.info(f"UUID: {UUID}")
    JIRA = args.jira
    if JIRA is None:
        JIRA = "N/A"
    else:
        logging.info(f"Associating run with Jira ticket {JIRA}")

    # set original Jenkins build url
    JENKINS_BUILD_URL = os.getenv("BUILD_URL")
    if not JENKINS_BUILD_URL:
        JENKINS_BUILD_URL = "N/A"

    # get YAML file with queries and set queries constant with data from YAML file
    YAML_FILE = args.yaml_file
    logging.info(f"YAML_FILE: {YAML_FILE}")
    try:
        with open(SCRIPT_DIR + "/queries/" + YAML_FILE, "r") as yaml_file:
            QUERIES = yaml.safe_load(yaml_file)
    except Exception as e:
        logging.error(f"Failed to read YAML file {YAML_FILE}: {e}")
        sys.exit(1)

    # get thanos URL from cluster
    raw_thanos_url = subprocess.run(
        [
            "oc",
            "get",
            "route",
            "thanos-querier",
            "-n",
            "openshift-monitoring",
            "-o",
            'jsonpath="{.spec.host}"',
        ],
        capture_output=True,
        text=True,
    ).stdout
    THANOS_URL = "https://" + raw_thanos_url[1:-1]
    logging.info(f"THANOS_URL: {THANOS_URL}")

    # get token from cluster
    TOKEN = subprocess.run(
        ["oc", "create", "token", "prometheus-k8s", "-n", "openshift-monitoring"],
        capture_output=True,
        text=True,
    ).stdout
    # try deprecated method in case first attempt fails
    if TOKEN == "":
        TOKEN = subprocess.run(
            ["oc", "sa", "new-token", "prometheus-k8s", "-n", "openshift-monitoring"],
            capture_output=True,
            text=True,
        ).stdout

    # log token or exit if no token could be found
    if TOKEN == "":
        logging.error(
            "No token could be found - ensure all the Prerequisite steps in the README were followed"
        )
        sys.exit(1)
    logging.info(f"TOKEN: {TOKEN}")

    # determine if data will be dumped locally or uploaded to Elasticsearch
    DUMP_ONLY = args.dump_only
    logging.info(f"Data will be dumped locally to {DATA_DIR}")
    if not DUMP_ONLY:
        if (ES_USERNAME is None) or (ES_PASSWORD is None):
            logging.error("Credentials need to be set to upload data to Elasticsearch")
            sys.exit(1)
        logging.info(f"Data will be uploaded to Elasticsearch")

    # begin main program execution
    main()
