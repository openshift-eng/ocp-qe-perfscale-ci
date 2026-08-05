import os
import time
from elasticsearch import Elasticsearch
import urllib3

# elasticsearch constants
ES_URL = os.environ.get('ES_URL','search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com')
ES_USERNAME = os.environ.get('ES_USERNAME')
ES_PASSWORD = os.environ.get('ES_PASSWORD')


def es_search_url(params, wildcard="", should="",must_not="", index='perfscale-jenkins-metadata',size=10, from_pos=0, es_url="", es_user="", es_pass=""):
    global ES_USERNAME, ES_URL, ES_PASSWORD
    ES_USERNAME = es_user
    ES_URL= es_url
    ES_PASSWORD = es_pass
    return es_search(params, wildcard, should,must_not, index,size, from_pos)

def es_search(params, wildcard="", should="",must_not="", index='perfscale-jenkins-metadata',size=10, from_pos=0):
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
        search_result = es.search(index=index, body={"query": {"bool": {"filter": filter_data}},  "size": size, "from": from_pos})
    except Exception as e: 
        print('exception ' +str(e))
    hits = []
    if "hits" in search_result.keys() and "hits" in search_result['hits'].keys():
        return search_result['hits']['hits']

    return hits

def delete_es_entry(id, index = 'perfscale-jenkins-metadata'):
    # create Elasticsearch object and attempt index
    es = Elasticsearch(
        [f'https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443']
    )
    
    es.delete(index=index, doc_type='_doc', id=id)

def delete_key(id, index, key_to_delete):

    es = Elasticsearch(
        [f'https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443']
    )

    es.update(
        index=index,
        id=id,
        body={"script": f"ctx._source.remove('{key_to_delete}')"}
    )

def update_data_to_elasticsearch(id, data_to_update, index = 'perfscale-jenkins-metadata'):
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

def upload_data_to_elasticsearch(item, index = 'perfscale-jenkins-metadata'):
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

#delete_es_entry("5F41vYYBRpj_T8Zahrtk")