#!/usr/bin/env python3

import os
from es_scripts import update_es_uuid


def find_workload_type( current_run_uuid):
    search_params = {
        "uuid": current_run_uuid
    }

    index = "perf_scale_ci*"
    
    hits = update_es_uuid.es_search(search_params, index=index)
    #print('hits ' + str(hits))
    if len(hits) > 0:
        workload_type = hits[0]['_source']['benchmark']
    else: 
        print('else')
        workload_type = find_workload_type_sub(current_run_uuid)
    return workload_type
    

def find_workload_type_sub( current_run_uuid):
    search_params = {
        "uuid": current_run_uuid
    }

    workload_index_map = { "kube-burner":"ripsaw-kube-burner" ,"ingress-perf":"ingress-perf*", "network-perf-v2":"k8s-netperf","router-perf":"router-test-results"}
    for k, v in workload_index_map.items(): 
        hits = update_es_uuid.es_search(search_params, index=v)
        #print('hits extra' + str(hits))
        if len(hits) > 0:
            return k
    return "Unknown"
    

def get_graphana(): 
    
    baseline_uuid = os.getenv("BASELINE_UUID")
    
    uuid = os.getenv("UUID")
    workload = find_workload_type( uuid)
    uuid_str = "&var-uuid=" + uuid
    if baseline_uuid != "" and baseline_uuid is not None:
        for baseline in baseline_uuid.split(","):
            uuid_str += "&var-uuid=" + baseline

    # data source for public dev es 
    # might want to be able to loop through multiple baseline uuids if more than one is passed

    grafana_url_ending="&from=now-1y&to=now&var-platform=AWS&var-platform=Azure&var-platform=GCP&var-platform=IBMCloud&var-platform=AlibabaCloud&var-platform=VSphere&var-platform=rosa"
    if workload == "ingress-perf":
        print(f"grafana url https://grafana.rdu2.scalelab.redhat.com:3000/d/nlAhmRyVk/ingress-perf?orgId=1&var-datasource=QE%20Ingress-perf{uuid_str}&var-termination=edge&var-termination=http&var-termination=passthrough&var-termination=reencrypt&var-latency_metric=avg_lat_us&var-compare_by=uuid.keyword&var-clusterType=rosa&var-clusterType=self-managed{grafana_url_ending}")

    elif workload == "k8s-netperf" or workload == "network-perf-v2":
        
        if "perfscale-dev" in os.getenv("ES_SERVER"):
            data_source = 'b7f1eb5f-4330-4a43-8be1-8ed1280a68a3'
        else: 
            data_source = "rKPTw9UVz"
        print(f"grafana url  https://grafana.rdu2.scalelab.redhat.com:3000/d/wINGhybVz/k8s-netperf?orgId=1&var-datasource={data_source}{uuid_str}&var-termination=edge&var-termination=http&var-termination=passthrough&var-termination=reencrypt&var-latency_metric=avg_lat_us&var-compare_by=uuid.keyword&var-clusterType=rosa&var-clusterType=self-managed{grafana_url_ending}")
    else:
        if "perfscale-dev" in os.getenv("ES_SERVER"):
            data_source = "C3f6SSfnk"
        else: 
            data_source = "QE%20kube-burner"
        print( f"grafana url https://grafana.rdu2.scalelab.redhat.com:3000/d/g4dJlkBnz3/kube-burner-compare?orgId=1&var-Datasource={data_source}&var-sdn=OVNKubernetes&var-workload={workload}&var-worker_nodes=&var-latencyPercentile=P99&var-condition=Ready&var-component=kube-apiserver{uuid_str}{grafana_url_ending}")



    # https://grafana.rdu2.scalelab.redhat.com:3000/d/D5E8c5XVz/kube-burner-report-mode?orgId=1&var-Datasource=QzcDu7T4z&var-platform=AWS&var-sdn=OVNKubernetes&var-clusterType=rosa&var-clusterType=self-managed&var-job=cluster-density-v2&var-workerNodesCount=120&var-ocpMajorVersion=4.17&var-ocpMajorVersion=4.18&var-compare_by=metadata.ocpMajorVersion&var-component=kube-apiserver&var-component=kube-controller-manager&var-node_roles=masters&var-node_roles=workers&var-node_roles=infra&from=now-60d&to=now&var-uuid=1af36ef8-6368-442d-bd75-55d74b7d9849&var-uuid=8d755c68-bf17-4b59-8a2f-f5b70749cc2d
get_graphana()
