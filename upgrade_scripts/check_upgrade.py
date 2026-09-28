#!/usr/bin/env python

import time
import yaml
import subprocess
import sys
import json

# Invokes a given command and returns the stdout
def invoke(command):
    try:
        output = subprocess.check_output(command, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        print("Status : FAIL", exc.returncode, exc.output)
        return exc.returncode, exc.output
    return 0, output

def set_max_unavailable(maxUnavailable):

    merge_json = '{"spec":{"maxUnavailable": %d }}' % maxUnavailable
    return_code, output = invoke(f"oc patch machineconfigpool/worker --type='merge' -p='{merge_json}'")
    if return_code != 0:
        print("Error occurred trying to set maxUnavialble nodes")

def get_sha_url(url,version):
    return_code, output = invoke("curl " + url)
    json_output = json.loads(output)
    for version_json in json_output['nodes']:
        if version_json['version'] == version:
            print(version_json['payload'])
            return
    print("")

def set_upstream_channel(channel, version):

    small_version = ".".join(version.split('.', 2)[:2])
    print('small v ' + str(small_version))
    if small_version == "4.9":
        patch_48_to_49()
    if small_version == "4.12":
        patch_411_to_412()
    merge_json = '{"spec":{"channel": "%s-%s" }}' % (channel, small_version)
    return_code, output = invoke(f"oc patch clusterversion/version --type='merge' -p='{merge_json}'")
    if return_code != 0:
        print("Error occurred trying to patch channel version")
    print('output ' + str(output))
    return_code, output = invoke("oc get clusterversion -ojson|jq .items[].spec")
    print('output ' + str(output))

def patch_48_to_49():
    merge_json = '{"data":{"ack-4.8-kube-1.22-api-removals-in-4.9":"true"}}'
    print('patch api')
    return_code, output = invoke(f"oc -n openshift-config patch cm admin-acks --type=merge -p='{merge_json}'")
    print('output: ' + str(output))

def patch_411_to_412(): 
    merge_json = '{"data":{"ack-4.11-kube-1.25-api-removals-in-4.12":"true"}}'
    print('patch api')
    return_code, output = invoke(f"oc -n openshift-config patch cm admin-acks --type=merge -p='{merge_json}'")
    print('output: ' + str(output))


def set_upstream_url(url):

    merge_json = '{"spec":{"upstream": "%s" }}' % url
    return_code, output = invoke(f"oc patch clusterversion/version --type='merge' -p='{merge_json}'")
    if return_code != 0:
        print("Error occurred trying to patch channel url")
    print('output ' + str(output))

def verify_version_in_channel_list(expected_version):
    return_code, output = invoke("oc adm upgrade")
    if return_code != 0:
        print("ERROR")

    split_output = output.split("Recommended updates")
    new_line_output = split_output[-1].split('\n')
    for line in new_line_output:

        space_line = line.split('  ')
        for s_line in space_line:
            if s_line != "" and expected_version == s_line.split(" ")[0].strip():
                print('expected version in list')
                return
    print("ERROR")

def get_upgrade_status(mcp_json):
    for mcp_status in mcp_json['status']['conditions']:
        if mcp_status['type'] == "Updating":
            print('Upgrade mcp status: ' + str(mcp_status['status']))
            return mcp_status['status']

def wait_for_mcp_upgrade(wait_num=90):
    counter = 0
    time.sleep(20)
    return_code, worker_str = invoke(f"oc get mcp worker -o json")
    worker_json = json.loads(worker_str)
    while get_upgrade_status(worker_json) != "False":
        time.sleep(20)
        return_code, worker_str = invoke(f"oc get mcp worker -o json")
        worker_json = json.loads(worker_str)
        print("MCP workers are updating, waiting 20 seconds")
        counter += 1
        if counter >= wait_num:
            print("#"*118)
            return_code, node_not_ready = invoke("oc get nodes | grep 'NotReady\|SchedulingDisabled'")
            print("Node list: " + str(node_not_ready))
            print("-"*118)
            return_code, mcp_status = invoke("oc get mcp")
            print("oc get mcp: " + str(mcp_status))
            print("-"*118)
            return_code, describe_mcp = invoke("for mcpname in `oc get mcp -oname`;do oc describe $mcpname;echo;echo '-----------------------------------------------------------'; done")
            print("oc describe mcp mcpname: " + str(describe_mcp))
            print("-"*118)
            print("ERROR, mcp workers are still updating after 30 minutes")
            print("#"*118)
            sys.exit(1)

def pause_machinepool_worker(pause_val):
    merge_json = '{"spec":{"paused": %s }}' % pause_val
    return_code, output = invoke(f"oc patch --type=merge --patch='{merge_json}' machineconfigpool/worker")
    if return_code != 0:
        print("Error occurred trying to pause machineconfigpool/worker")
    print('output ' + str(output))

def check_cluster_version():

    return_code, output = invoke("oc get clusterversion -o yaml")
    if return_code == 0:
        #parse output to get cluster version and status?
        output = yaml.load(output, Loader=yaml.FullLoader)

        for condition in output['items'][0]['status']['conditions']:
            if condition['type'] == "Progressing":
                print(f"Progressing status {condition['message']}")
                break
        for status_history in output['items'][0]['status']['history']:
            if status_history['state'] == "Completed":
                print(f"Actual version {status_history['version']}")
                return status_history['version']
            else:
                print(f"State of version: {status_history['state']} {status_history['version']}")
        return output
    else:
        print("Error getting clusterversion")
    return ""

def get_release_accepted():
    # Returns the ReleaseAccepted condition of the clusterversion as (status, message).
    # The CVO sets it to False when it cannot retrieve/verify the requested payload,
    # for example when --to-image points at a tag that does not exist.
    return_code, output = invoke("oc get clusterversion -o json")
    if return_code != 0:
        return "", ""
    try:
        cv_json = json.loads(output)
        for condition in cv_json['items'][0]['status']['conditions']:
            if condition['type'] == "ReleaseAccepted":
                return condition['status'], condition.get('message', '')
    except (ValueError, KeyError, IndexError) as exc:
        print(f"Could not read the ReleaseAccepted condition: {exc}")
    return "", ""

# Main function
def check_upgrade(expected_cluster_version, wait_num=300, rejected_wait_num=20):
    print(f"Starting upgrade check to {expected_cluster_version}")
    upgrade_version = check_cluster_version()
    j = 0
    rejected = 0
    # Will wait for up to 2.5 hours... might need to increase or decrease - need to observe.
    while j < wait_num:
        if upgrade_version == expected_cluster_version:
            wait_for_nodes_ready()
            wait_for_co_ready()
            return 0
        # Bail out early instead of polling for hours when the CVO refuses the payload
        accepted_status, accepted_message = get_release_accepted()
        if accepted_status == "False":
            rejected += 1
            print(f"ReleaseAccepted is False ({rejected}/{rejected_wait_num}): {accepted_message}")
            if rejected >= rejected_wait_num:
                print("#"*118)
                print(f"ERROR, the CVO did not accept the requested payload: {accepted_message}")
                print("The upgrade never started, check the --to-image pullspec passed to 'oc adm upgrade'")
                print("#"*118)
                sys.exit(1)
        else:
            rejected = 0
        upgrade_version = check_cluster_version()
        time.sleep(30)
        j += 1
    print("#"*118)
    print(f"ERROR, the cluster is still on {upgrade_version} and did not reach {expected_cluster_version} in time")
    print("#"*118)
    sys.exit(1)

def wait_for_co_ready(wait_num=30):

    counter = 0
    while counter < wait_num:
        return_code, count_not_ready = invoke("oc get co |sed '1d'|grep -v 'openshift-samples'|grep -v '.*True.*False.*False' | wc -l | xargs")
        if return_code == 0:
            if str(count_not_ready).strip() == "0":
                return
        print("Waiting 10 seconds for co to not be available")
        time.sleep(10)
        counter += 1
    print("ERROR: Co were still available and not progressing after 5 minutes")


def get_not_ready_node(wait_num=30):
    # could be a couple seconds inbetween nodes upgdating/going not ready
    counter = 0
    # Will wait up to 5 minutes to find a NotReady/SchedulingDisabled Node
    while counter < wait_num:
        return_code, count_not_ready = invoke("oc get nodes | grep 'NotReady\|SchedulingDisabled'| head -n 1")
        str_count = str(count_not_ready).strip()
        if return_code == 0 and str_count != "":
            return str_count
        print("Waiting 10 seconds to see if new node starts updating")
        time.sleep(10)
        counter += 1
    return "DONE"


def wait_for_nodes_ready(wait_num=30):

    counter = 0
    last_not_ready_node = get_not_ready_node()
    while counter < wait_num:
        cur_not_ready_node = get_not_ready_node()
        if cur_not_ready_node == "DONE":
            print("No new node has been updating in the last 5 minutes")
            return
        print("Waiting 30 seconds for nodes to become ready and scheduling enabled")
        time.sleep(30)
        counter += 1
        if cur_not_ready_node != last_not_ready_node:
            last_not_ready_node = cur_not_ready_node
            counter = 0
    print("ERROR: Nodes were still not ready and scheduling enabled after 30 minutes")

def wait_for_replicas(machine_replicas, machine_name, wait_num=60):
    counter = 0
    return_code, replicas = invoke(f"oc get {machine_name} -n openshift-machine-api -o jsonpath={{.status.availableReplicas}}")
    while replicas != machine_replicas:
        time.sleep(5)
        return_code, replicas = invoke(f"oc get {machine_name} -n openshift-machine-api -o jsonpath={{.status.availableReplicas}}")
        print("Replicas didn't match, waiting 5 seconds")
        counter += 1
        if counter >= wait_num:
            print("ERROR, replica count doesn't match expected after 5 minutes")
            sys.exit(1)

    counter = 0
    return_code, not_ready_node = invoke("oc get nodes | grep 'NotReady' | wc -l | xargs")
    while int(not_ready_node) != 0:
        time.sleep(5)
        print("Nodes not ready yet, waiting 5 seconds")
        return_code, not_ready_node = invoke("oc get nodes | grep 'NotReady' | wc -l | xargs")
        counter += 1
        if counter >= wait_num:
            print("ERROR, nodes are still not ready after 5 minutes")
            sys.exit(1)
    print("Machine sets have correct replica count and all nodes are ready")
