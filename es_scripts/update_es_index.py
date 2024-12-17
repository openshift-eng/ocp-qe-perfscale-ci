import os
import time
from elasticsearch import Elasticsearch
import update_es_uuid


# elasticsearch constants
ES_URL = 'search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com'
ES_USERNAME = os.getenv('ES_USERNAME')
ES_PASSWORD = os.getenv('ES_PASSWORD')


def delete_key(id, index, key_to_delete):

    es = Elasticsearch(
        [f'https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443']
    )

    es.update(
        index=index,
        id=id,
        body={"script": f"ctx._source.remove('{key_to_delete}')"}
    )

def update_data_to_elasticsearch(params, index, new_index):
    ''' updates captured data in RESULTS dictionary to Elasticsearch
    '''

    start = time.time()
    matched_docs = update_es_uuid.es_search(params, index=index, size=50,from_pos=10)
 
   
   # print('doc length' + str(len(matched_docs[0]['_source'])))
    for item in matched_docs:
        param_uuid = {"uuid": item['_source']['uuid']}
        found_uuid = update_es_uuid.es_search(param_uuid, index=new_index)
        
        if len(found_uuid) == 0:
            print('find uui' + str(found_uuid))
            response = upload_data_to_elasticsearch(item["_source"], new_index)
            print(f"Response back was {response}")
            #break
    
    end = time.time()
    elapsed_time = end - start

    # return elapsed time for upload if no issues
    return elapsed_time

def upload_data_to_elasticsearch(item, index):
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
# to_update = {"profile": "IPI-on-AWS.install.yaml"}
# update_data_to_elasticsearch("2l41vYYBRpj_T8Zagru2", to_update)
# update_data_to_elasticsearch("4F41vYYBRpj_T8ZahLvF", to_update)
# update_data_to_elasticsearch("7F41vYYBRpj_T8ZairsN", to_update)
# update_data_to_elasticsearch("5F41vYYBRpj_T8Zahrtk", to_update)


params={"workload":'ovn-live-migration'}
new_index="ovn-live-migration"
old_index="ripsaw-kube-burner*"
update_data_to_elasticsearch(params,  old_index, new_index)
#delete_es_entry("5F41vYYBRpj_T8Zahrtk")