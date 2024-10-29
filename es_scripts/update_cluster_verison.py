import update_es_uuid
import time 


index="krkn-telemetry"

params={'cloud_infrastructure':'AWS'}

must_not={"field": "cluster_version"}

#"must_not": [
        # {
        #   "exists": {
        #     "field": "cluster_version"
        #   }
        # }

i = 0
size = 60
from_pos = 0
while i < 20: 
    print('from pos' + str(from_pos))
    es_search_all=update_es_uuid.es_search(params,must_not=must_not,index=index, size=size,from_pos=from_pos)
    #print('search all' + str(es_search_all))
    for es_search in es_search_all:
        
        if "cluster_version" in es_search["_source"]: 
            print('continue')
            continue
        os_version = es_search["_source"]['node_summary_infos'][0]["os_version"]
        # "Red Hat Enterprise Linux CoreOS 417.94.202410180656-0"

        #418.94.20240906 2250-0
        numbers = os_version.split(' ')[-1]
        if "Plow" in numbers: 
            numbers = os_version.split(' ')[-2]
        numbers = numbers.split(".")

        print('numbers ' + str(os_version
                               ))
        #4.17.0-0.nightly-2024-10-21-185738
        version = numbers[0][0] + '.' + numbers[0][1:] + ".0-0.nightly-" + numbers[2][:4] + "-" + numbers[2][4:6] +"-" + numbers[2][6:8]  +"-" + numbers[2][8:12] + numbers[2][13:14]
        print('version: ' + str(es_search['_id']) + " " +str(version))
        data_to_update= {'cluster_version': version}
        update_es_uuid.update_data_to_elasticsearch(es_search['_id'],data_to_update,index)
        time.sleep(2)
    i+=1 
    from_pos = size * i