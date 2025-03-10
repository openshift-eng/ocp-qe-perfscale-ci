import gspread
from oauth2client.service_account import ServiceAccountCredentials
import subprocess
import csv 
import yaml
import calendar 
from datetime import datetime
import os
import sys

# Invokes a given command and returns the stdout
def invoke(command):
    output = ""
    try:
        output = subprocess.check_output(command, shell=True,
                                         universal_newlines=True)
    except Exception:
        print("Failed to run %s" % (command))
    return output

def add_new_worksheet(row,gsheet_key_location, gsheet_location): 
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
       gsheet_key_location, scope
    )
    
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_url(gsheet_location)
    timestamp = datetime.today().strftime("%m/%d/%Y-%H%M%S")
    title = "ProwCadence" + str(timestamp)
    sheet.add_worksheet(title=title, rows=100, cols=20)
    ws = sheet.worksheet(title)
    ws.append_rows(row,value_input_option="USER_ENTERED")
    print(f"New worksheet tab '{title}' is created in {gsheet_location}")

def write_csv(row):
    # append to file
        
    with open(final_csv, "w") as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=",")
        for r in row: 
            csv_writer.writerow(r)

def get_cron_in_words(cron_string):

    if " " not in cron_string:
        return f"{cron_string}"
    cron_split = cron_string.split(" ")
    # index 0 Minute of hour
    # index 1 Hour of day
    # index 2 Day of month
    # index 3 Month
    # index 4 day of week

    end_string = ""
    day_of_month = cron_split[2] 
    if day_of_month != "*":
        #print('day of month' + str(day_of_month) + str(type(day_of_month)))
        if "/" in day_of_month:
            day = day_of_month.split('/')[-1]
            day_string = f"every {day} days"
        elif "," in day_of_month:
            day = day_of_month.split(',')
            day_string = f"on days {day} of the month"
        else: 
            day_string = f"on day {day_of_month} of the month"
        #print("day string" + str(day_string))
        end_string = day_string
    if cron_split[4] != "*":
        if "," in cron_split[4]:
            day = cron_split[4].split(',')
            day_of_week = ""
            i =0 
            for d in day: 
                day_of_week += calendar.day_name[int(d) -1 ]
                i +=1
                if i < len(day): 
                    day_of_week += " and "
                
        elif "-" in cron_split[4]:
            day = cron_split[4].split('-')
            day_of_week = ""
            i = 0
            for d in day: 
                day_of_week += calendar.day_name[int(d) -1]
                if i == 0: 
                    day_of_week += " to "
                i +=1
        else: 
            day_of_week = calendar.day_name[int(cron_split[4]) -1 ]
        #print('day of week' + str(day_of_week))
        end_string = "on " + day_of_week + "s"
    return f"At {cron_split[1]}, {end_string}"


def get_replicas(yaml_file):

    if "workflow" in yaml_file['steps'].keys() and "single-node" in yaml_file['steps']['workflow']: 
        return "1"
    if "env" in yaml_file['steps'].keys(): 
        if "REPLICAS" in yaml_file['steps']['env'].keys():
            return yaml_file['steps']['env']['REPLICAS']
        elif "WORKER_REPLICA_COUNT" in yaml_file['steps']['env'].keys(): 
            return yaml_file['steps']['env']['WORKER_REPLICA_COUNT']
        elif "COMPUTE_NODE_REPLICAS" in yaml_file['steps']['env'].keys(): 
            return yaml_file['steps']['env']['COMPUTE_NODE_REPLICAS']
        elif "ARO_WORKER_COUNT" in yaml_file['steps']['env'].keys(): 
            return yaml_file['steps']['env']['ARO_WORKER_COUNT']
    return "3"

def get_multiaz(yaml_file):
    if "env" in yaml_file['steps'].keys(): 
        if "MULTI_AZ" in yaml_file['steps']['env'].keys():
            return yaml_file['steps']['env']['MULTI_AZ']
    return "true"


def get_profile(yaml_file):
    if "cluster_profile" in yaml_file['steps'].keys():      
        return yaml_file['steps']['cluster_profile']
    return "no profile"

def get_cloud_type(yaml_file):
    
    if  "workflow" in yaml_file['steps'].keys(): 
        if "hcp" in yaml_file['steps']['workflow']: 
            return "hcp"
        elif "rosa" in yaml_file['steps']['workflow']:
            return "rosa"
        elif "aro" in yaml_file['steps']['workflow']:
            return "aro"
    if "cluster_profile" in yaml_file['steps'].keys():
        if "aws" in yaml_file['steps']['cluster_profile']:
            return "aws"
        elif "gcp" in yaml_file['steps']['cluster_profile']:
            return "gcp"
        elif "azure" in yaml_file['steps']['cluster_profile']:
            return "azure"
    return "Unset"

def verify_channel(test):
    if "env" in test['steps'].keys(): 
        if "CHANNEL_GROUP" in test['steps']['env'].keys(): 
            return test['steps']['env']["CHANNEL_GROUP"]
    return ""

def get_master_type(test):
    if "env" in test['steps'].keys(): 
        if "CHANNEL_GROUP" in test['steps']['env'].keys(): 
            return test['steps']['env']["CHANNEL_GROUP"]
    return ""

def get_worker_type(test):
    if "env" in test['steps'].keys(): 
        if "COMPUTE_MACHINE_TYPE" in test['steps']['env'].keys(): 
            return test['steps']['env']["COMPUTE_MACHINE_TYPE"]
        elif "COMPUTE_NODE_TYPE" in test['steps']['env'].keys():
            return test['steps']['env']["COMPUTE_NODE_TYPE"]
    return "default"

def get_job_history(file_name, test_name):
    job_url = "https://prow.ci.openshift.org/job-history/gs/origin-ci-test/logs/periodic-ci-"
    
    job_url += file_name.replace("__","-").replace('.yaml', "") + "-" + test_name

    job_cell = f'=HYPERLINK("{job_url}","{test_name}")'
    return job_cell

def get_release(yaml_file):
    if "releases" in yaml_file: 
        if "latest" in yaml_file['releases'].keys():
            for v1 in yaml_file['releases']['latest'].values():
                if "stream" in v1.keys(): 
                    return v1['version'], v1['stream']
                return v1['version'], v1['channel']
        for v in yaml_file['releases'].values():
            print('v = ' + str(v))  
            
            for v1 in v.values():
                if "stream" in v1.keys(): 
                    return v1['version'], v1['stream']
                return v1['version'], v1['channel']
    return "",""

def get_cron(yaml_file): 
    
    if "cron" in yaml_file.keys(): 
        return yaml_file['cron']
    return False

def get_arch_type(yaml_file):
    if "env" in yaml_file['steps'].keys(): 
        if "OCP_ARCH" in yaml_file['steps']['env'].keys():
            return yaml_file['steps']['env']['OCP_ARCH']
    return "x86"

def get_profile_type(yaml_file):
    if "env" in yaml_file['steps'].keys(): 
        if "PROFILE_TYPE" in yaml_file['steps']['env'].keys():
            return yaml_file['steps']['env']['PROFILE_TYPE']
    return "none"

def test_profile(folder_path, fileName):
    with open(folder_path + "/" + fileName, "r") as f:
        yaml_file = yaml.safe_load(f)
    version, stream = get_release(yaml_file)
    final_row = []
    if version: 
        for test in yaml_file['tests']:
            
            cron_cadence = get_cron(test)
            if cron_cadence is False: 
                continue
            cron_in_words = get_cron_in_words(cron_cadence)
            worker_count = get_replicas(test)
            type = get_cloud_type(test)
            arch_type =get_arch_type(test)
            channel_test = verify_channel(test)
            if channel_test != "": 
                stream = channel_test
            job_url = get_job_history(fileName, test['as'])

            worker_size = get_worker_type(test)
            profile_set = get_profile_type(test)
            profile_name = get_profile(test)
            row = [test['as'], profile_name, type, arch_type, version, stream, worker_count, worker_size, profile_set, '"' + cron_cadence +'"', cron_in_words, job_url]
            final_row.append(row)
    return final_row


#Get Google sheet secret
gsheet_key_location = os.getenv('GSHEET_KEY_LOCATION')
gsheet_location = os.getenv('GSHEET_LOCATION', 'https://docs.google.com/spreadsheets/d/1TM73n4Y6zKRQjvCX8zFM0LwYxChdsncTEGPHpdsS9Ig')
jobs_folder_location = os.getenv('JOBS_FOLDER_LOCATION', 'openshift-eng/ocp-qe-perfscale-ci')

if not gsheet_key_location:
    print("GSHEET_KEY_LOCATION is not set.")
    sys.exit(1)
try:
    with open(gsheet_key_location, "r") as file:
        pass
except FileNotFoundError:
    print(f"File '{gsheet_key_location}' not found. Please set it correctly as GSHEET_KEY_LOCATION env viriable.")
    sys.exit(1)
except IOError:
    print(f"Error: File '{gsheet_key_location}' could not be opened.")
    sys.exit(1)

final_csv = "periodic.csv"
invoke("rm -rf release_master")
invoke("mkdir release_master")
invoke("cd release_master; git clone https://github.com/openshift/release.git --depth=1")
jobs_folder_path=f"./release_master/release/ci-operator/config/{jobs_folder_location}"


# Check if the folder exists
if os.path.exists(jobs_folder_path) and os.path.isdir(jobs_folder_path):
    # Check if the folder is not empty
    if any(os.listdir(jobs_folder_path)):
        pass
    else:
        print(f"The folder '{jobs_folder_path}' exists but is empty.")
        sys.exit(1)
else:
    print(f"The folder '{jobs_folder_path}' does not exist or is not a directory.")
    sys.exit(1)

file_names = invoke("ls " + jobs_folder_path)

all_rows = []
all_rows.append(["Test Name", "Profile", "Cloud Type", "Arch Type", "Version", "Stream type", "Worker_count", "Worker Size", "Profile", 'Cron Cadence', "Cron In Words", "Job history Url"])
for file_name in file_names.split():
    if file_name != "OWNERS":
        print("file name " + str(file_name))
        file_name_rows = test_profile(jobs_folder_path, file_name)
        all_rows.extend(file_name_rows)

write_csv(all_rows)
add_new_worksheet(all_rows, gsheet_key_location, gsheet_location)