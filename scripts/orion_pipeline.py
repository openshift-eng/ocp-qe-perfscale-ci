import os
import time
from elasticsearch import Elasticsearch
import urllib3
import subprocess
from elasticsearch.exceptions import AuthenticationException
import urllib3
from requests.auth import HTTPBasicAuth
import warnings

# elasticsearch constants
ES_URL = os.environ.get('ES_URL','https://search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com')
ES_USERNAME = os.environ.get('ES_USERNAME')
ES_PASSWORD = os.environ.get('ES_PASSWORD')
ES_INDEX= "perf_scale_ci*"

ORION_CMD = "/path/to/orion --uuid {} --config /path/to/config.yaml"
warnings.filterwarnings("ignore", category=UserWarning)

# Disable SSL warnings
urllib3.disable_warnings()
urllib3.logging.captureWarnings(False)


def get_es_client():
    return Elasticsearch(
        hosts=[ES_URL],
        http_auth=(ES_USERNAME, ES_PASSWORD),
        use_ssl=True,
        verify_certs=False,  # Disable SSL verification if needed
    )

def es_search_url(params, wildcard="", should="",must_not="", index='perf_scale_ci*',size=10, from_pos=0, es_url="", es_user="", es_pass=""):
    global ES_USERNAME, ES_URL, ES_PASSWORD
    ES_USERNAME = es_user
    ES_URL= es_url
    ES_PASSWORD = es_pass
    return es_search(params, wildcard, should,must_not, index,size, from_pos)

def es_search(params, wildcard="", should="",must_not="", index='perf_scale_ci*',size=10, from_pos=0):
    urllib3.disable_warnings()
    urllib3.logging.captureWarnings(False)
    # create Elasticsearch object and attempt index
    global ES_URL
    if "http" in ES_URL: 
        ES_URL = ES_URL.split('//')[1]
    es = Elasticsearch(
        [f'https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}'], verify_certs=False, use_ssl=True
    )
    filter_data = []
    filter_data.append({
          "match_all": {}
        })
    for p, v in params.items():
        match_data= {}
        match_data['match_phrase'] = {}
        match_data['match_phrase'][p] = v
        filter_data.append(match_data)
    
    # match a wildcard character
    must_not_list_data = []
    if wildcard != "": 
        for p, v in wildcard.items():
            wildcard_data= {}
            wildcard_data['wildcard'] = {}
            wildcard_data['wildcard'][p] = v
            filter_data.append(wildcard_data)
    # should exist
    if should != "": 
        bool_should = {}
        bool_should['bool'] = {}
        bool_should['bool']['should'] = []
        #print('should' + str(should))
        for p, v in should.items():
            should_data= {}
            should_data['should_phrase'] = {}
            should_data['should_phrase'][p] = v
            bool_should['bool']['should'].append(bool_should)

    # must not exist
    if must_not != "": 
        #print('must_not' + str(must_not))
        for p, v in must_not.items():
            must_not_data= {}
            must_not_data['exists'] = {}
            must_not_data['exists'][p] = v
            must_not_list_data.append(must_not_data)
        #print('must not' + str(must_not))
    #print("f ilter_data " + str(filter_data))
    try: 
        # search_result = es.search(index=index, body={"query": {"bool": {"filter": filter_data}},  "size": size, "from": from_pos})
        
        query = {
            "bool": {
                "filter": []  # Modify this if needed
            }
        }

        search_result = es.search(
            index="perf_scale_ci*",
            query=query,  # Moved 'query' out of 'body'
            size=100
        )
    except Exception as e: 
        print('exception ' +str(e))
    hits = []
    if "hits" in search_result.keys() and "hits" in search_result['hits'].keys():
        return search_result['hits']['hits']

    return hits


def update_data_to_elasticsearch(id, data_to_update, index = 'perf_scale_ci*'):
    ''' updates captured data in RESULTS dictionary to Elasticsearch
    '''

    # create Elasticsearch object and attempt index
    es = Elasticsearch(
        [f'https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443']
    )

    start = time.time()
    
    doc = es.get(index=index, doc_type='_doc', id=id)
    #print('doc '+ str(doc))
    for k,v in data_to_update.items(): 
        doc['_source'][k] = v
    es.update(index=index, doc_type='_doc', id=id, body={"doc": doc['_source']
    })
    ##print(f"Response back was {response}")
    end = time.time()
    elapsed_time = end - start

    # return elapsed time for upload if no issues
    return elapsed_time

def upload_data_to_elasticsearch(item, index = 'perf_scale_ci*'):
    ''' uploads captured data in RESULTS dictionary to Elasticsearch
    '''

    # create Elasticsearch object and attempt index
    es = Elasticsearch(
        [f'https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443']
    )

    start = time.time()
    print(f"Uploading item {item} to index {index} in Elasticsearch")
    response = es.index(
        index=index,
        body=item
    )
    print(f"Response back was {response}")
    end = time.time()
    elapsed_time = end - start

    # return elapsed time for upload if no issues
    return elapsed_time

# Function to fetch the latest UUIDs from Elasticsearch
def fetch_uuids():
    es = get_es_client()

    try:
        
        search_result = es_search(index="perf_scale_ci*")
        
        # response = es.search(index="perf_scale_ci*", body=query)

        print("🔍 Debug: Response from Elasticsearch:")
        print(search_result)  # Print the raw response

        if search_result and "hits" in search_result and "hits" in search_result["hits"]:
            uuids = [hit["_source"].get("uuid") for hit in search_result["hits"]["hits"] if "uuid" in hit["_source"]]
            print(f"✅ Found UUIDs: {uuids}")
            return uuids
        else:
            print("⚠️ No hits found in Elasticsearch.")
            return []

    except AuthenticationException as e:
        print(f"❌ Authentication Error: {e}")
    except Exception as e:
        print(f"❌ Error fetching UUIDs from Elasticsearch: {e}")
    return []

# Function to run Orion against each UUID
def run_orion_for_uuids(uuids):
    for uuid in uuids:
        print(f"Running Orion for UUID: {uuid}")
        cmd = ORION_CMD.format(uuid)
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"Orion execution successful for UUID: {uuid}")
        except subprocess.CalledProcessError as e:
            print(f"Error running Orion for UUID {uuid}: {e}")

# Function to update results in Elasticsearch
def update_results(uuid, results):
    es = get_es_client()
    try:
        es.update(index=ES_INDEX, id=uuid, body={"doc": results})
        print(f"Updated results in Elasticsearch for UUID: {uuid}")
    except Exception as e:
        print(f"Failed to update results for UUID {uuid}: {e}")

def main():
    print("Fetching UUIDs from Elasticsearch...")
    uuids = fetch_uuids()
    if not uuids:
        print("No UUIDs found for analysis.")
        return
    
    print("Running Orion for fetched UUIDs...")
    run_orion_for_uuids(uuids)

    print("Updating results in Elasticsearch...")
    for uuid in uuids:
        results = {"status": "completed", "orion_timestamp": time.time()}
        update_results(uuid, results)

if __name__ == "__main__":
    main()
