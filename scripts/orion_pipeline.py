#!/usr/bin/env python3

import os
import subprocess
import requests
import json
import logging
from es_scripts.update_es_uuid import fetch_uuids_from_es

ELASTICSEARCH_URL = "https://opensearch.app.intlab.redhat.com"
INDEX_NAME = "perf_scale_ci*"
ORION_SCRIPT_PATH = "/path/to/cloud-bulldozer/orion/orion.py"
RESULTS_INDEX = "orion_results"

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# RUN ORION AGAINST THE UUIDs
def run_orion(uuid):
    """Run Orion for a given UUID."""
    logging.info(f"Running Orion for UUID: {uuid}")
    cmd = ["python3", ORION_SCRIPT_PATH, "--uuid", uuid]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logging.info(f"Orion output: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Orion failed for UUID {uuid}: {e.stderr}")
        return None

# STORE RESULTS BACK TO ELASTICSEARCH
def store_results(uuid, orion_output):
    """Store Orion analysis results in ElasticSearch."""
    if not orion_output:
        logging.warning(f"No results to store for UUID {uuid}")
        return

    document = {
        "uuid": uuid,
        "orion_output": orion_output,
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(f"{ELASTICSEARCH_URL}/{RESULTS_INDEX}/_doc", headers=headers, json=document)

    if response.status_code in [200, 201]:
        logging.info(f"Successfully stored results for UUID {uuid}")
    else:
        logging.error(f"Failed to store results for UUID {uuid}: {response.text}")

def main():
    # Fetch UUIDs from ElasticSearch
    uuids = fetch_uuids_from_es()

    if not uuids:
        logging.warning("No UUIDs found. Exiting...")
        return

    # Run Orion on each UUID and store results
    for uuid in uuids:
        orion_output = run_orion(uuid)
        store_results(uuid, orion_output)

if __name__ == "__main__":
    main()
