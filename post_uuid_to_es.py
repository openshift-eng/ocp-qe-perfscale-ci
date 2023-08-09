#!/usr/bin/env python3

import os
import sys
import json
import time
import urllib3
import pathlib
import jenkins
import logging
import argparse
import datetime
import subprocess
import coloredlogs
from elasticsearch import Elasticsearch
import helper_uuid
import update_es_uuid

# disable SSL and warnings
os.environ['PYTHONHTTPSVERIFY'] = '0'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# directory constants 
ROOT_DIR = str(pathlib.Path(__file__).parent.parent)
SCRIPT_DIR = ROOT_DIR + '/scripts'
DATA_DIR = ROOT_DIR + '/data'

USER = None
DEBUG = False
RESULTS ={}

# prometheus query constants
START_TIME = None
END_TIME = None

# jenkins env constants
JENKINS_URL = 'https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/'
JENKINS_JOB = os.getenv("JENKINS_JOB_PATH")
jenkins_build = os.getenv("JENKINS_JOB_NUMBER")
JENKINS_SERVER = None
UUID = None

# elasticsearch constants
ES_URL = 'search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com'
ES_USERNAME = os.getenv('ES_USERNAME')
ES_PASSWORD = os.getenv('ES_PASSWORD')
DUMP = False
UPLOAD_FILE = ''
CI_PROFILE = os.getenv('CI_PROFILE')
PROFILE_SCALE_SIZE = os.getenv('PROFILE_SCALE_SIZE')


TEST_STATUS = os.getenv("CI_STATUS")
METRIC_NAME = ""
def run(command):
    try:
        output = subprocess.check_output(command, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        print("Status : ", command, exc.output)
        return exc.returncode, exc.output
    return 0, output.strip()

def get_jenkins_params(): 
    # collect data from Jenkins server
    try:
        build_info = JENKINS_SERVER.get_build_info(JENKINS_JOB, int(jenkins_build))
        logging.info(f"Jenkins Build Info: {build_info}")
        build_actions = build_info['actions']
        build_parameters = None
        for action in build_actions:
            if action.get('_class') == 'hudson.model.ParametersAction':
                build_parameters = action['parameters']
                break
        if build_parameters is None:
            raise Exception("No build parameters could be found.")
        return build_parameters
    except Exception as e:
        logging.error(f"Failed to collect Jenkins build parameter info: {e}")
    return []

def set_es_obj_info():
    ''' gathers information about Jenkins env
        if build parameter data cannot be collected, only command line data will be included
    '''
    print('setting es obj')
    # intialize info object
    iso_timestamp = datetime.datetime.utcnow()
    version = helper_uuid.get_oc_version()
    network_type= helper_uuid.get_net_type()
    arch_type = helper_uuid.get_arch_type()
    worker_count = helper_uuid.get_node_count("node-role.kubernetes.io/worker=")
    print('ci profile ' + str(CI_PROFILE))
    if CI_PROFILE == "": 
        print('if')
        profile = helper_uuid.get_scale_profile_name(version, arch_type, network_type, worker_count)[0]
        profile_size = ""
    else:
        print('else')
        profile = CI_PROFILE
        profile_size = PROFILE_SCALE_SIZE
    print("profile " + str(profile) + str(profile_size))
    if profile != "": 
        info = {
            "metric_name": METRIC_NAME,
            "status": TEST_STATUS,
            "data_type": "metadata",
            "iso_timestamp": iso_timestamp,
            "jenkins_job_name": JENKINS_JOB,
            "jenkins_build_num": jenkins_build,
            "profile": profile,
            "profile_size": profile_size,
            "ocp_version": version,
            "user": USER,
            "network_type": network_type,
            "arch_type": arch_type,
            "worker_count": worker_count,
            "master_size": helper_uuid.get_node_type("node-role.kubernetes.io/master="),
            "worker_size": helper_uuid.get_node_type("node-role.kubernetes.io/worker="),
            "infra_node_count": helper_uuid.get_node_count("node-role.kubernetes.io/infra="), 
            "workload_node_count": helper_uuid.get_node_count("node-role.kubernetes.io/workload="),
            "LAUNCHER_VARS": os.getenv('VARIABLES_LOCATION'),
            "fips_enabled": helper_uuid.get_fips(),
            "across_az": helper_uuid.get_multi_az("node-role.kubernetes.io/worker=")
        }
        return info
    return None

def get_scale_ci_data(): 
    info = {}
    build_parameters = get_jenkins_params()
    try: 
        for param in build_parameters:
            del param['_class']
            if param.get('name') == 'WORKLOAD':
                info['workload'] = str(param.get('value'))
            if param.get('name') == 'VARIABLE':
                info['parameters'] = int(param.get('value'))
    except Exception as e:
        logging.error(f"Failed to collect Jenkins build parameter info: {e}")
    info["uuid"] =  os.getenv('UUID')
    return info

def get_net_perf_v2_data(): 
    info = {}
    build_parameters = get_jenkins_params()
    try: 
        for param in build_parameters:
            del param['_class']
            if param.get('name') == 'WORKLOAD_TYPE':
                info['WORKLOAD_TYPE'] = str(param.get('value'))
    except Exception as e:
        logging.error(f"Failed to collect Jenkins build parameter info: {e}")
    info["uuid"] =  os.getenv('UUID')
    return info

def get_ingress_perf_data(): 
    info = {}
    build_parameters = get_jenkins_params()
    try: 
        for param in build_parameters:
            del param['_class']
            if param.get('name') == 'CONFIG':
                info['CONFIG'] = str(param.get('value'))
    except Exception as e:
        logging.error(f"Failed to collect Jenkins build parameter info: {e}")
    info["uuid"] =  os.getenv('UUID')
    return info

def get_nightly_reg_data(): 
    info = {}
    build_parameters = get_jenkins_params()
    try: 
        for param in build_parameters:
            del param['_class']
            if param.get('name') == 'TESTS_TO_RUN':
                info['tests_ran'] = str(param.get('value'))
    except Exception as e:
        logging.error(f"Failed to collect Jenkins build parameter info: {e}")
    info["failed_tests"] = os.getenv('FAILED_JOBS')
    return info


# This is a work in progress and needs to be updated with proper data
def get_loaded_up_data(): 
    info = {}
    build_parameters = get_jenkins_params()
    try: 
        for param in build_parameters:
            del param['_class']
            if param.get('name') == 'TESTS_TO_RUN':
                info['tests_ran'] = str(param.get('value'))
    except Exception as e:
        logging.error(f"Failed to collect Jenkins build parameter info: {e}")
    info["failed_tests"] = os.getenv('FAILED_JOBS')
    return info

def get_upgrade_data(): 
    info = {}
    build_parameters = get_jenkins_params()
    try: 
        for param in build_parameters:
            del param['_class']
            if param.get('name') == 'UPGRADE_VERSION':
                info['upgrade_version'] = str(param.get('value'))
    except Exception as e:
        logging.error(f"Failed to collect Jenkins build parameter info: {e}")
    info["failed_tests"] = os.getenv('FAILED_JOBS')
    return info

def dump_data_locally(timestamp, partial=False):
    ''' writes captured data in RESULTS dictionary to a JSON file
        file is saved to 'data_{timestamp}.json' in DATA_DIR system path if data is complete
        file is saved to 'partial_data_{timestamp}.json' in DATA_DIR system path if data is incomplete
    '''

    # ensure data directory exists (create if not)
    pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

    # write prometheus data to data directory
    if not partial:
        with open(DATA_DIR + f'/data_{timestamp}.json', 'w') as data_file:
            json.dump(RESULTS, data_file)
    else:
        with open(DATA_DIR + f'/partial_data_{timestamp}.json', 'w') as data_file:
            json.dump(RESULTS, data_file)

    # return if no issues
    return None


def upload_data_to_elasticsearch():
    ''' uploads captured data in RESULTS dictionary to Elasticsearch
    '''

    # create Elasticsearch object and attempt index
    es = Elasticsearch(
        [f'https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443']
    )

    start = time.time()
    for item in RESULTS['data']:
        index = 'perfscale-jenkins-metadata'
        logging.info(f"Uploading item {item} to index {index} in Elasticsearch")
        response = es.index(
            index=index,
            body=item
        )
        logging.info(f"Response back was {response}")
    end = time.time()
    elapsed_time = end - start

    # return elapsed time for upload if no issues
    return elapsed_time

def main():

    # log success if no issues
    logging.info(f"Data captured successfully")

    # either dump data locally or upload it to Elasticsearch
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    try:
        elapsed_time = upload_data_to_elasticsearch()
        logging.info(f"Elasticsearch upload completed in {elapsed_time} seconds")

    except Exception as e:
        logging.error(f"Error uploading to Elasticsearch server: {e}\nA local dump to {DATA_DIR}/data_{timestamp}.json will be done instead")
        dump_data_locally(timestamp)
        # using exit code of 2 here so that Jenkins pipeline can unqiuely identify this error
        sys.exit(2)

    # exit if no issues
    sys.exit(0)


def search_for_entry(info): 
    search_params = {
        "metric_name": METRIC_NAME,
        "jenkins_job_name": info['jenkins_job_name'],
        "jenkins_build_num": info['jenkins_build_num'],
    }

    hits = update_es_uuid.es_search(search_params)
    
    if len(hits) == 0: 
        # return false, no entry was found 
        return False
    else: 
        # returning true that entry was found for the job already
        return True


if __name__ == '__main__':

    # initialize argument parser
    parser = argparse.ArgumentParser(description='PerfScale Post to Elasticsearch tool')

    # set logging flags
    parser.add_argument("--debug", default=False, action='store_true', help='Flag for additional debug messaging')

    # set standard mode flags
    standard = parser.add_argument_group("Standard Mode", "Connect to an OCP cluster and gather data")
    standard.add_argument("--baseline", type=str, help='Update baseline uuid if it doesnt exist')
    standard.add_argument("--user", type=str, help='User that ran the test')
    # parse arguments
    args = parser.parse_args()

    # set logging config
    DEBUG = args.debug
    if DEBUG:
        logging.basicConfig(level=logging.info)
        coloredlogs.install(level='DEBUG', isatty=True)
    else:
        logging.basicConfig(level=logging.INFO)
        coloredlogs.install(level='INFO', isatty=True)
    
    baseline = args.baseline
    workload = os.getenv('WORKLOAD')
    if str(baseline) == "true": 
        # find matching profile
        # if data already exists, don't post 
        METRIC_NAME = "base_line_uuids"
        base_line_uuid = helper_uuid.find_uuid(workload, METRIC_NAME)
        print('baseline ' + str(base_line_uuid))
        if base_line_uuid is not False:
            logging.info("Baseline UUID for this configuration is already set")
            sys.exit(0)
    else: 
        # here we can find the profile information if it matches but will still want to post results either way 
        METRIC_NAME = "jenkinsEnv"

    USER = args.user
    RESULTS['data'] = []
    # sanity check that kubeconfig is set
    result = subprocess.run(['oc', 'whoami'], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error("Could not connect to cluster - ensure all the Prerequisite steps in the README were followed")
        sys.exit(1)

    # determine UUID
    info = set_es_obj_info()

    helper_uuid.run("unset https_proxy http_proxy")
    # check if Jenkins arguments are valid and if so set constants
    raw_jenkins_job = JENKINS_JOB
    raw_jenkins_build = jenkins_build
    if all(v is None for v in [raw_jenkins_job, raw_jenkins_build]):
        JENKINS_SERVER = None
    elif any(v is None for v in [raw_jenkins_job, raw_jenkins_build]):
        logging.error("JENKINS_JOB and jenkins_build must all be used together or not at all")
        sys.exit(1)
    else:

        logging.info(f"Associating run with Jenkins job {JENKINS_JOB} build number {jenkins_build}")
        try:
            JENKINS_SERVER = jenkins.Jenkins(JENKINS_URL)
        except Exception as e:
            logging.error("Error connecting to Jenkins server: ", e)
            sys.exit(1)

    if search_for_entry(info): 
        logging.info(f"Jenkins build job: {JENKINS_JOB} was already found logged in ElasticSearch")
        sys.exit(1)

    if workload == "nightly-regression":
        jenkins_info = get_nightly_reg_data()
        for k,v in jenkins_info.items(): 
            info[k] = v
    elif workload == "upgrade":
        jenkins_info = get_upgrade_data()
        for k,v in jenkins_info.items(): 
            info[k] = v
    elif workload == "loaded-upgrade": 
        jenkins_info = get_loaded_up_data()
        for k,v in jenkins_info.items(): 
            info[k] = v
    elif "network-perf" in workload:
        jenkins_info = get_net_perf_v2_data()
        for k,v in jenkins_info.items(): 
            info[k] = v
    elif "ingress-perf" == workload: 
        jenkins_info = get_ingress_perf_data()
        for k,v in jenkins_info.items(): 
            info[k] = v
    elif "nightly" not in workload:
        jenkins_info = get_scale_ci_data()
        for k,v in jenkins_info.items(): 
            info[k] = v
    RESULTS['data'].append(info)
    

    if (ES_USERNAME is None) or (ES_PASSWORD is None):
        logging.error("Credentials need to be set to upload data to Elasticsearch")
        sys.exit(1)
    logging.info(f"Data will be uploaded to Elasticsearch")

    # begin main program execution
    main()