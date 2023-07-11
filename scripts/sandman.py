#!/usr/bin/env python3

import re
import sys
import time
import json
import pathlib
import argparse
import datetime

# constants 
ROOT_DIR = str(pathlib.Path(__file__).parent.parent)
DATA_DIR = ROOT_DIR + '/data'
WORKLOAD_OUT_FILE = ''
SANDMAN_OUT_FILE_TYPE = ''

def main():

    # read workload out file
    with open(WORKLOAD_OUT_FILE, 'r') as out_file:
        workload_logs = out_file.read()
    
    uuid_exists = True
    iterations_exists = True

    # initialize regexs based on file type
    if "kube-burner-ocp" in WORKLOAD_OUT_FILE:
        base_regex = 'time="(\d+-\d+-\d+ \d+:\d+:\d+)".*'
        starttime_regex = base_regex + 'Starting'
        endtime_regex = base_regex + 'Exiting'
        strptime_filter = '%Y-%m-%d %H:%M:%S'
        workload_regex = 'Job '
        workload_end_regex = ':'

        # capture and log strings representations of workload name
        workload_first_str = workload_logs.split(workload_regex)[1]
        workload_type = workload_first_str.split(workload_end_regex)[0]
        uuid_regex = 'UUID (.*)"'
        if "node-density" in workload_type:
            iterations_start = " --pods-per-node="
            iterations_end = " "
        else: 
            iterations_start = " --iterations="
            iterations_end = " "

    elif "kube-burner" in WORKLOAD_OUT_FILE:
        base_regex = 'time="(\d+-\d+-\d+ \d+:\d+:\d+)".*'
        starttime_regex = base_regex + 'Starting'
        endtime_regex = base_regex + 'Exiting'
        strptime_filter = '%Y-%m-%d %H:%M:%S'
        workload_regex = 'Workload: '
        workload_end_regex = '\n'

        # capture and log strings representations of workload name
        workload_type = workload_logs.split(workload_regex)[1].split(workload_end_regex)[0]
        uuid_regex = 'UUID: (.*)"'

        # find iterations 
        if "node-density" in workload_type:
            iterations_start = "Pods per node: "
            iterations_end = "\n"
        else: 
            iterations_start = "Job iterations: "
            iterations_end = "\n"
        
    elif "ingress_router" in WORKLOAD_OUT_FILE:
        base_regex = '([a-zA-z]{3}\s+\d+ \d+:\d+:\d+ [a-zA-z]{3} \d+).*'
        starttime_regex = base_regex + 'Testing'
        endtime_regex = base_regex + 'Enabling'
        strptime_filter = '%b %d %H:%M:%S %Z %Y'
        uuid_regex = 'UUID: (.*)"'
        iterations_exists = False
        workload_type = "router-perf"

    elif "network-perf-v2" in WORKLOAD_OUT_FILE:
        base_regex = 'time="(\d+-\d+-\d+ \d+:\d+:\d+)".*'
        starttime_regex = base_regex + ' Reading'
        endtime_regex = base_regex + 'Rendering'
        strptime_filter = '%Y-%m-%d %H:%M:%S'
        uuid_regex = 'UUID (.*)"'
        iterations_exists = False
        workload_type = "network-perf-v2"
    
    # capture and log strings representations of start and end times
    starttime_string = re.findall(starttime_regex, workload_logs)[0]
    
    print(f"starttime_string: {starttime_string}")

    try: 
        endtime_string = re.findall(endtime_regex, workload_logs)[0]
    except: 
        # if can't find the end time properly (error during run)
        # find the last time posted in workload_logs file
        endtime_string = re.findall(base_regex, workload_logs)[-1]
    print(f"endtime_string: {endtime_string}")

    # convert string times to unix timestamps
    starttime_timestamp = int(datetime.datetime.strptime(starttime_string, strptime_filter).replace(tzinfo=datetime.timezone.utc).timestamp())
    endtime_timestamp = int(datetime.datetime.strptime(endtime_string, strptime_filter).replace(tzinfo=datetime.timezone.utc).timestamp())
    print(f"starttime_timestamp: {starttime_timestamp}")
    print(f"endtime_timestamp: {endtime_timestamp}")

    # construct JSON of workload data
    workload_data = {
        "workload_type": str(workload_type),
        "starttime_string": str(starttime_string),
        "endtime_string": str(endtime_string),
        "starttime_timestamp": str(starttime_timestamp),
        "endtime_timestamp": str(endtime_timestamp)
    }

    # Depending on the workload, we want to find the uuid (not existent for network-perf-v2)
    # Specific regex configurations set based on file type above 
    if uuid_exists:
        try: 
            uuid = re.findall(uuid_regex, workload_logs)[0].split('"')[0]
            print(f"uuid: {uuid}")
            workload_data['uuid'] = str(uuid)
        except: 
            print("No uuid found")

    # Depending on the workload, we want to find the number of iterations 
    # Specific regex configurations set based on file type above 
    if iterations_exists:
        # rework to use an end
        iterations = workload_logs.split(iterations_start)[1].split(iterations_end)[0]
        print(f"iterations: {iterations}")
        workload_data['iteratons'] = str(iterations)

    # ensure data directory exists (create if not)
    pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

    # write sandman data out to data directory with the specified file type
    if SANDMAN_OUT_FILE_TYPE == 'json':
        with open(DATA_DIR + f'/workload.json', 'w') as data_file:
            json.dump(workload_data, data_file)
    else:
        workload_env_vars = ""
        for k,v in workload_data.items():
            workload_env_vars += "export " + k + "='" + v + "'\n"
        with open(DATA_DIR + f'/workload.sh', 'w') as data_file:
            data_file.write(workload_env_vars)

    # exit if no issues
    sys.exit(0)

if __name__ == '__main__':

    # initialize argument parser
    parser = argparse.ArgumentParser(description='Mr. Sandman: Master of Time and the Knowledge bound by it')

    # set argument flags
    parser.add_argument("--file", type=str, required=True, help='Workload out file to parse')
    parser.add_argument("--output", type=str, default='json', choices=['json', 'sh'], help="Sandman out file type to generate - defaults to 'json'")

    # parse arguments
    args = parser.parse_args()
    WORKLOAD_OUT_FILE = args.file
    SANDMAN_OUT_FILE_TYPE = args.output

    # begin main program execution
    main()
