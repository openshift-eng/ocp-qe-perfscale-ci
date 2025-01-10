#!/usr/bin/env python3

import os
from es_scripts import update_es_uuid


def find_workload_type( current_run_uuid):
    search_params = {
        "uuid": current_run_uuid
    }

    index = os.getenv("es_metadata_index")
    
    hits = update_es_uuid.es_search(search_params, index=index)
    print('hits ' + str(hits))
    if len(hits) <= 0:
        #print('else')
        workload_type = find_workload_type_sub(current_run_uuid)
        print('workload type' + str(workload_type))
        if workload_type == "Unknown" and "intlab" not in os.environ.get("ES_URL"): 
            
            es_metadata_index="ospst-perf-scale-ci*"
            if os.getenv("ES_USERNAME_INTERNAL") is not None and os.getenv("ES_PASSWORD_INTERNAL") is not None:
                os.environ["ES_USERNAME"] = os.getenv("ES_USERNAME_INTERNAL", None)
                os.environ["ES_PASSWORD"] =  os.getenv("ES_PASSWORD_INTERNAL", None)
                # try finding in internal es

                ES_URL = os.environ["ES_URL"] = "https://opensearch.app.intlab.redhat.com"
                
                hits = update_es_uuid.es_search_url(search_params, es_url=ES_URL, es_pass=os.getenv("ES_PASSWORD_INTERNAL"), es_user=os.getenv("ES_USERNAME_INTERNAL"),index=es_metadata_index)
                print('hits ' + str(hits))
            else: 
                print("internal username and password not set")

    if len(hits) == 0: 
        print("No data entry was found for that UUID")
        return "Not Found"
    return hits[0]['_source']
    

def find_workload_type_sub( current_run_uuid):
    search_params = {
        "uuid": current_run_uuid
    }


    if "intlab" in os.environ.get("ES_URL"): 
        workload_index_map = { "kube-burner":"ospst-ripsaw-kube-burner*" ,"ingress-perf":"ospst-ingress-perf*", "network-perf-v2":"ospst-k8s-netperf*"}
    else: 
        workload_index_map = { "kube-burner":"ripsaw-kube-burner*" ,"ingress-perf":"ingress-perf*", "network-perf-v2":"k8s-netperf*","router-perf":"router-test-results"}
    for k, v in workload_index_map.items(): 
        hits = update_es_uuid.es_search(search_params, index=v)
        print('hits extra' + str(hits))
        if len(hits) > 0:
            return k
    return "Unknown"
    

def get_graphana(): 
    
    baseline_uuid = os.environ.get("BASELINE_UUID")
    
    uuid = os.environ.get("UUID")
    workload_details = find_workload_type( uuid)
    if workload_details != "Not Found":
        workload = workload_details["benchmark"]
        uuid_str = "&var-uuid=" + uuid
        baseline_workload_details= []
        if baseline_uuid != "" and baseline_uuid is not None:
            for baseline in baseline_uuid.split(","):
                uuid_str += "&var-uuid=" + baseline
                baseline_workload_details.append(find_workload_type(baseline))


        worker_count = f"&var-workerNodesCount={workload_details['workerNodesCount']}"
        # data source for public dev es 
        # might want to be able to loop through multiple baseline uuids if more than one is passed
        major_version = "&var-ocpMajorVersion=" + str(workload_details['releaseStream'][:4])
        for baseline_details in baseline_workload_details:
            if baseline_details['releaseStream'][:4] not in major_version:
                major_version += "&var-ocpMajorVersion=" + str(baseline_details['releaseStream'][:4])
        grafana_url_ending=f"{worker_count}&from=now-1y&to=now&var-platform=AWS&var-platform=Azure&var-platform=GCP&var-platform=IBMCloud&var-platform=AlibabaCloud&var-platform=VSphere&var-platform=rosa&var-clusterType=rosa&var-clusterType=self-managed"
        if workload == "ingress-perf":
            if "intlab" in os.environ.get("ES_URL"): 
                data_source = "be0f4aff-4122-43cf-95dd-fd51c012a208"
            else: 
                data_source = "beefdfd9-800e-430c-afef-383032aa2d1f"
            
            grafana_url_ending += f"&var-infraNodesType={workload_details['infraNodesType']}"
            print(f"grafana url https://grafana.rdu2.scalelab.redhat.com:3000/d/d6105ff8-bc26-4d64-951e-56da771b703d/ingress-perf?orgId=1&var-datasource=beefdfd9-800e-430c-afef-383032aa2d1f&var-Datasource={data_source}{uuid_str}=&var-termination=edge&var-termination=http&var-termination=passthrough&var-termination=reencrypt&var-latency_metric=avg_lat_us&var-compare_by=uuid.keyword{major_version}{grafana_url_ending}")
            print(f"grafana report mode link:  https://grafana.rdu2.scalelab.redhat.com:3000/d/df906760-b4c0-44cc-9ecb-586cf39f9bab/ingress-perf-v2-report-mode?orgId=1&var-datasource={data_source}{uuid_str}&var-ocpMajorVersion=All&var-uuid=&var-termination=All&var-latency_metric=avg_lat_us&var-compare_by=ocpMajorVersion.keyword&var-all_uuids=All{grafana_url_ending}")
        elif workload == "k8s-netperf" or workload == "network-perf-v2":
            
            if "intlab" in os.environ.get("ES_URL"):
                data_source = 'abc72863-3b49-47d5-98d1-357a9559afea'
            else: 
                data_source = "rKPTw9UVz"
            print(f"grafana url  https://grafana.rdu2.scalelab.redhat.com:3000/d/wINGhybVz/k8s-netperf?orgId=1&var-datasource={data_source}{uuid_str}&var-termination=edge&var-termination=http&var-termination=passthrough&var-termination=reencrypt&var-latency_metric=avg_lat_us&var-compare_by=uuid.keyword&var-workerNodesCount=9&from=now-1y&to=now&var-platform=All&var-clusterType=rosa&var-clusterType=self-managed&var-workerNodesType=All&var-hostNetwork=All&var-service=All&var-parallelism=All&var-throughput_profile=All&var-latency_profile=All&var-messageSize=All&var-driver=netperf")
        else:
            if "intlab" in os.environ.get("ES_URL"):
                data_source = "ab3f14e6-a50f-4d52-93fa-a5076794f864"
            else: 
                data_source = "QzcDu7T4z"
            print( f"grafana url https://grafana.rdu2.scalelab.redhat.com:3000/d/g4dJlkBnz3/kube-burner-compare?orgId=1&var-Datasource={data_source}&var-sdn=OVNKubernetes&var-workload={workload}&var-latencyPercentile=P99&var-condition=Ready&var-component=kube-apiserver{uuid_str}{grafana_url_ending}")

            print(f"grafana report mode link: https://grafana.rdu2.scalelab.redhat.com:3000/d/D5E8c5XVz/kube-burner-report-mode?orgId=1&var-Datasource={data_source}&var-sdn=OVNKubernetes&var-clusterType=rosa&var-clusterType=self-managed&var-job={workload}{major_version}&var-compare_by=metadata.ocpMajorVersion&var-component=kube-apiserver&var-component=kube-controller-manager&var-node_roles=masters&var-node_roles=workers&var-node_roles=infra&to=now{uuid_str}{grafana_url_ending}")

    # 
get_graphana()
