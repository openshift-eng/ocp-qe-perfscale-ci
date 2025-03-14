#!/usr/bin/env python3

import os
import sys
import json
import urllib3
import pathlib
import jenkins
import logging
import argparse
import datetime
import subprocess
import coloredlogs
from helpful_scripts.scripts import find_cluster_data
from helpful_scripts.es_scripts import help_find_es

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
JENKINS_URL = 'https://jenkins-csb-openshift-qe-mastern.dno.corp.redhat.com/'
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


METRIC_NAME = ""
current_run_data = {}
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

def set_es_obj_info(uuid_data):
    ''' gathers information about Jenkins env
        if build parameter data cannot be collected, only command line data will be included
    '''
    print('setting es obj')
    # intialize info object
    iso_timestamp = datetime.datetime.utcnow()
    version = uuid_data['ocpVersion']
    network_type= uuid_data['networkType']
    arch_type = find_cluster_data.get_arch_type()
    worker_count = int(uuid_data['workerNodesCount'])
    print('ci profile ' + str(CI_PROFILE))
    if CI_PROFILE == "": 
        print('if')
        profile = find_cluster_data.get_scale_profile_name(version, arch_type, network_type, worker_count)[0]
        profile_size = ""
    else:
        print('else')
        profile = CI_PROFILE
        profile_size = PROFILE_SCALE_SIZE
    print("profile " + str(profile) + str(profile_size))
    if profile != "": 
        info = {
            "metric_name": METRIC_NAME,
            "clusterType": uuid_data['clusterType'],
            "status": uuid_data['jobStatus'],
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
            "master_size": uuid_data['masterNodesType'],
            "worker_size": uuid_data['workerNodesType'],
            "infra_node_count": uuid_data['infraNodesCount'],
            "fips_enabled": find_cluster_data.get_fips(),
            "across_az": find_cluster_data.get_multi_az("node-role.kubernetes.io/worker="),
            "platform": uuid_data['platform']
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

def main():

    # log success if no issues
    logging.info(f"Data captured successfully")

    # either dump data locally or upload it to Elasticsearch
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    try:
        elapsed_time = help_find_es.post_result_data(RESULTS)
        logging.info(f"Elasticsearch upload completed in {elapsed_time} seconds")

    except Exception as e:
        logging.error(f"Error uploading to Elasticsearch server: {e}\nA local dump to {DATA_DIR}/data_{timestamp}.json will be done instead")
        dump_data_locally(timestamp)
        # using exit code of 2 here so that Jenkins pipeline can unqiuely identify this error
        sys.exit(2)

    # exit if no issues
    sys.exit(0)


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
    workload = os.getenv('BENCHMARK') 
    current_run_uuid =  os.getenv('UUID')

    current_run_data = help_find_es.find_uuid_data(workload,current_run_uuid) 
    print("Current run data details" + str(current_run_data))
    if "jobStatus" in current_run_data.keys() and current_run_data['jobStatus'] != "success":
        logging.info("Current run failed, not posting result as baseline")
        sys.exit(0) 
    if str(baseline) == "true": 
        # find matching profile
        # if data already exists, don't post 
        METRIC_NAME = "base_line_uuids"
        base_line_uuid = help_find_es.find_uuid(workload, METRIC_NAME, current_run_data)
        print('baseline ' + str(base_line_uuid))
        if base_line_uuid is not False:
            logging.info("Baseline UUID for this configuration is already set")
            sys.exit(0)
    else: 
        # here we can find the profile information if it matches but will still want to post results either way 
        # path no longer being called
        METRIC_NAME = "jenkinsEnv"

    USER = args.user
    RESULTS['data'] = []
    # sanity check that kubeconfig is set
    result = subprocess.run(['oc', 'whoami'], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error("Could not connect to cluster - ensure all the Prerequisite steps in the README were followed")
        sys.exit(1)

    # determine UUID
    info = set_es_obj_info(current_run_data)

    find_cluster_data.run("unset https_proxy http_proxy")
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

    info['workload'] = workload
    if "network-perf" in workload:
        jenkins_info = get_net_perf_v2_data()
        for k,v in jenkins_info.items(): 
            info[k] = v
    elif "ingress-perf" == workload: 
        jenkins_info = get_ingress_perf_data()
        for k,v in jenkins_info.items(): 
            info[k] = v
    elif "nightly" not in workload and "upgrade" not in workload:
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
