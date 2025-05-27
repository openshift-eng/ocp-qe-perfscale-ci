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

api_file_list = 'apilist'
invoke("mkdir "+ str(api_file_list))

folder_name = "apidocs/"
api_docs_file_names = invoke("ls "+ str(folder_name))[1].split("\n")
print("api_docs_file_names" + str(api_docs_file_names))
for file_name in api_docs_file_names:
    if file_name != "":
        with open(folder_name + file_name) as f: 
            file_str = f.read()
        file_json = json.loads(file_str)
        path_list= []
        for path in file_json['paths'].keys(): 
            path_list.append(path)
        with open(api_file_list +"/"+ file_name, "a+") as r: 
            path_list_str = '\n'.join(path_list)
            r.write(path_list_str)
