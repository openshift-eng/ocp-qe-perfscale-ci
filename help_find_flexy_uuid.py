from collections import ChainMap
import logging
import sys
import jenkins
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pandas as pd
import json 
import coloredlogs
import urllib3
import os
import helper_uuid
import time 
import yaml
from yaml.loader import SafeLoader

# jenkins env constants
JENKINS_URL = 'https://jenkins-csb-openshift-qe-mastern.dno.corp.redhat.com/'
JENKINS_JOB = "ocp-common/Flexy-install"
jenkins_build = None
JENKINS_SERVER = None
UUID = None

# disable SSL and warnings
os.environ['PYTHONHTTPSVERIFY'] = '0'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

kb_workload_types_nd = [
    "cluster-density", 
    "pod-density", 
    "pod-density-heavy", 
    "node-density", 
    "max-namespaces",
    "node-density-heavy",
    "router-perf"
]


platforms = [
    "aws",
    "azure",
    "gcp",
    "alicloud",
    "ibmcloud",
    "vsphere", 
    "nutanix", 
    "baremetal",
    "osp"
]

google_sheet_account="/Users/prubenda/.secrets/perf_sheet_service_account.json"

def get_flexy_params(jenkins_build):
    # check if Jenkins arguments are valid and if so set constants
    try:
        JENKINS_SERVER = jenkins.Jenkins(JENKINS_URL)
        print('properly setting jenkins server')

    except Exception as e:
        print("Error connecting to Jenkins server: ", e)
        sys.exit(1)
    # collect data from Jenkins server
    try:
        
        info= {}
        info['flexy_id'] = jenkins_build
        build_info = JENKINS_SERVER.get_build_info(JENKINS_JOB, jenkins_build)
        build_actions = build_info['actions']
        build_parameters = None
        for action in build_actions:
            if action.get('_class') == 'hudson.model.ParametersAction':
                build_parameters = action['parameters']
                break
        if build_parameters is None:
            raise Exception("No build parameters could be found.")
        for param in build_parameters:
            del param['_class']
            if param.get('name') == 'VARIABLES_LOCATION':
                info['VARIABLES_LOCATION'] = str(param.get('value'))
            if param.get('name') == "LAUNCHER_VARS":
                info['LAUNCHER_VARS'] = str(param.get('value'))
    except Exception as e:
        logging.error(f"Failed to collect Jenkins build parameter info: {e}")
        return None

    return info

def get_grafana_uuid(base_dataframe, uuid):

    row = base_dataframe.loc[base_dataframe['Grafana URL'] == uuid]

    return row.iloc[0]

def get_uuid(base_dataframe, uuid):

    row = base_dataframe.loc[base_dataframe['UUID'] == uuid]

    return row.iloc[0]


def get_kube_burner_data_from_sheet(workload):
    scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
    ]

    credentials = ServiceAccountCredentials.from_json_keyfile_name(google_sheet_account, scopes) #access the json key you downloaded earlier
    file = gspread.authorize(credentials) # authenticate the JSON key with gspread

    sheet = file.open_by_url("https://docs.google.com/spreadsheets/d/1uiKGYQyZ7jxchZRU77lsINpa23HhrFWjphsqGjTD-u4/edit?usp=sharing")

    ws = sheet.worksheet(workload)

    base_dataframe = pd.DataFrame(ws.get_all_records())

    return base_dataframe



def get_data(found_uuid, base_dataframe):
    org_info = {}
    if found_uuid is not None and found_uuid != "":
        # once got uuid, find flexy id
        
        if workload == "router-perf":
            row_data = get_uuid( base_dataframe, found_uuid)
        else: 
            row_data = get_grafana_uuid( base_dataframe, found_uuid)
            if "node-density" in workload: 
                org_info['parameters'] = row_data['PODS_PER_NODE']
            else: 
                org_info['parameters'] = row_data['Params']
        org_info['ci_job_num'] = row_data['Scale Ci Job']
        flexy_id = row_data['Flexy Id']
        org_info['flexy_build'] = flexy_id
        org_info['uuid'] = found_uuid
        org_info['cloud'] = row_data['Cloud']
        org_info['ocp_version'] = row_data['OCP Version'].strip()
        org_info['arch_type'] = row_data['Arch Type']
        org_info['network_type'] = row_data['Network Type']
        if org_info['network_type'].lower() == "ovn": 
            org_info['network_type'] = "OVNKubernetes"
        else: 
            org_info['network_type'] = "OpenShiftSDN"
        org_info['worker_count'] = row_data['Worker Count']
        # with flexy id get parameters to new list/file with workload type 
        info = get_flexy_params(int(flexy_id))
        if info is not None: 
            if "VARIABLES_LOCATION" in info.keys() and info['VARIABLES_LOCATION'] != "":
                if "arm" in info['VARIABLES_LOCATION'].lower():
                    org_info['arch_type'] = "arm64"
                if "ovn" in info['VARIABLES_LOCATION'].lower():
                    info['network_type'] = "OVNKubernetes"
            if "LAUNCHER_VARS" in info.keys() and info['LAUNCHER_VARS'] != "":
                no_quote_vars = info['LAUNCHER_VARS'].replace('"',"").replace("'","")
                if no_quote_vars != "":
                    split_vars = no_quote_vars.split('\n')
                    json_launcher_vars = {}
                    print('split vars' + str(split_vars))
                    for var in split_vars: 
                        var_s = var.split(':')
                        if var_s[0] != "":
                            if len(var_s) > 2: 
                                var_s[1] =  var_s[1] + ":" + var_s[2]
                            json_launcher_vars[var_s[0]] = var_s[1].replace(' ',"")
                    if "vm_type_workers" in json_launcher_vars.keys():
                        org_info['worker_size'] = json_launcher_vars['vm_type_workers']
                    if "vm_type_masters" in json_launcher_vars.keys():
                        org_info['master_size'] = json_launcher_vars['vm_type_masters']
                    if "OVNKubernetes" in info['LAUNCHER_VARS'].lower():
                        org_info['network_type'] = "OVNKubernetes"
                    if "networkType" in json_launcher_vars.keys():
                        org_info['network_type'] = json_launcher_vars['networkType']
                print('flexy info foun d ' + str(info))

            org_info["LAUNCHER_VARS"] = info['LAUNCHER_VARS']
        else: 
            org_info["LAUNCHER_VARS"] = ""
        if org_info['worker_count'] > 50: 
            org_info["infra_node_count"] = 3
            org_info["workload_node_count"] = 1
        else: 
            org_info["infra_node_count"] = 0
            org_info["workload_node_count"] = 0
        org_info['profile'], org_info['worker_size'], org_info['master_size'], org_info["LAUNCHER_VARS"] = helper_uuid.get_scale_profile_name(org_info['ocp_version'] ,org_info['cloud'], org_info['arch_type'], org_info['network_type'],org_info['worker_count'],org_info['LAUNCHER_VARS'])
        # read through
    return org_info
        
def parse_profile_type(version, w_count, w_items, base_dataframe): 
    print("w_items " + str(w_items))
    found_uuid = ""
    sub_workload = {}
    for profile in w_items.keys(): 
        print("profile ")
        found_uuid = read_json[version][w_count][profile]
        org_info = get_data(found_uuid, base_dataframe)
        if "profile" in org_info.keys():
            sub_workload[org_info['profile']] = org_info
    return sub_workload

def parse_net_arch_type(version, w_count, w_items, base_dataframe): 
    found_uuid = ""
    sub_workload = {}
    for net_type, net_items in w_items.items(): 

        for arch_type in net_items.keys(): 
            found_uuid = read_json[version][w_count][net_type][arch_type]
            org_info = get_data(found_uuid, base_dataframe)
            if "profile" in org_info.keys():
                sub_workload[org_info['profile']] = org_info
    return sub_workload

def read_uuid(workload, platform, read_json):
    
    base_dataframe = get_kube_burner_data_from_sheet(workload)
    workload_list = {}
    for version, v_items in read_json.items():
        workload_list[version] = {}
        for w_count, w_items in v_items.items():
            workload_list[version][str(w_count)] = {}
            print('type ' +str( type(w_items.values())))
            if type(w_items.values()) is dict.values: 
                sub_workload_list = parse_net_arch_type(version, w_count, w_items, base_dataframe)
            else: 
                sub_workload_list = parse_profile_type(version, w_count, w_items, base_dataframe)
            for k, v in sub_workload_list.items(): 
                workload_list[version][str(w_count)][k] = v
    with open(workload + "/" + platform + "flexy.json", "w") as fr:
        fr.write(json.dumps(workload_list))

logging.basicConfig(level=logging.INFO)
coloredlogs.install(level='INFO', isatty=True)

for workload in kb_workload_types_nd: 
    for platform in platforms:
        with open(workload + "/" + platform + ".json", "r") as fr:
            read_str =fr.read()
            read_json = json.loads(read_str)
        read_uuid(workload, platform, read_json)
        time.sleep(10)