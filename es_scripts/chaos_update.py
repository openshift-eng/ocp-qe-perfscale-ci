import update_es_uuid
import json 
ids=["XStsmZEBPJqRxZ0XWz26","Wyv-kJEBPJqRxZ0XaD35"]
ids=["zO95D5EBjXIeP7FHSwnd","Nip2D5EBPJqRxZ0XAFt9"]
index="krkn-telemetry"
params={"_id":"XStsmZEBPJqRxZ0XWz26"}

params={"run_uuid":'fd1984a4-97da-4ce7-9a28-95b7a8cc8cf9'}
#es_search=update_es_uuid.es_search(params,index=index )[0]


# update_es_uuid.delete_key(ids[0], index, "cluster_version")
# update_es_uuid.delete_key(ids[1], index, "cluster_version")
# del es_search['_source']["cluster_version"]
# print('es search 1' + str(es_search))
# update_es_uuid.update_data_to_elasticsearch(es_search['_id'], es_search, index)

with open("run.json","r+") as f:
    es_search = json.loads(f.read())

    update_es_uuid.upload_data_to_elasticsearch(es_search,index)