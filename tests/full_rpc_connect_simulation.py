#!/usr/bin/env python

"""
This script is for generating a 2-party end-to-end run of the PySyft REST-RPC 
service. Detailed here are all the necessary payload submissions that are
required to be submitted to `http://<ttp_host>:<ttp_port>/ttp/connect/...` in
order to initialise and register for a PySyft REST-RPC project.

Note: Ensure that a TTP container is already up before running this script
"""

####################
# Required Modules #
####################

# Generic/Built-in
import logging

# Libs
import requests

##################
# Configurations #
##################

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# Relevant IDs
project_id = "test_project"
expt_id = "test_experiment"
run_id = "test_run"
participant_id_1 = "test_worker_1"
participant_id_2 = "test_worker_2"

# Relevant Connection Endpoints
ttp_host = "0.0.0.0"#"localhost"
ttp_port = 5000#15000
base_ttp_connect_url = f"http://{ttp_host}:{ttp_port}/ttp/connect"

project_upload_url = f"{base_ttp_connect_url}/projects"
project_retrieval_url = f"{base_ttp_connect_url}/projects/{project_id}"

expt_upload_url = f"{project_retrieval_url}/experiments"
expt_retrieval_url = f"{project_retrieval_url}/experiments/{expt_id}"

run_upload_url = f"{expt_retrieval_url}/runs"
run_retrieval_url = f"{expt_retrieval_url}/runs/{run_id}"

participant_upload_url = f"{base_ttp_connect_url}/participants"
participant_1_retrieval_url = f"{base_ttp_connect_url}/participants/{participant_id_1}"
participant_2_retrieval_url = f"{base_ttp_connect_url}/participants/{participant_id_2}"

registration_1_url = f"{participant_1_retrieval_url}/projects/{project_id}/registration"
registration_2_url = f"{participant_2_retrieval_url}/projects/{project_id}/registration"

tags_1_url = f"{registration_1_url}/tags"
tags_2_url = f"{registration_2_url}/tags"

# Project Simulation
test_project = {
    "project_id": project_id,
    "incentives": {
        "tier_1": ["test_worker_1"],
        "tier_2": ["test_worker_2"]
    }
}

# Experiment Simulation
test_experiment = {
    "expt_id": expt_id,
    "model": [
        {
            "activation": "sigmoid",
            "is_input": True,
            "l_type": "linear",
            "structure": {
                "bias": True,
                "in_features": 28,
                "out_features": 1
            }
        }
    ]
}

# Run Simulation
test_run = {
    "run_id": run_id,
    "input_size": 28,
    "output_size": 1,
    "batch_size": 32,
    "rounds": 2,
    "epochs": 1,
    "lr": 0.15,
    "weight_decay": 0.01,
    "mu": 0.1,
    "l1_lambda": 0.2,
    "l2_lambda": 0.3,
}

# Participant Simulation
test_participant_1 = {
    "participant_id": participant_id_1,
    "id": "test_worker_1",
    "host": "172.17.0.2", #"127.0.0.1", #"localhost",#"172.19.152.152",  # 0.0.0.0 only for local simulation!
    "port": 8020,#8021,#8020,    
    "log_msgs": False,
    "verbose": False,
    "f_port": 5000,#5001#5000      # Only required if custom port is required (i.e. local)
}

test_participant_2 = {
    "participant_id": participant_id_2,
    "id": "test_worker_2",
    "host": "172.17.0.3",#"127.0.0.1", #"localhost", #"127.0.0.1",#"172.19.152.153",  # 0.0.0.0 only for local simulation!
    "port": 8020,#8022,#8020,    
    "log_msgs": False,
    "verbose": False,
    "f_port": 5000,#5002#5000      # Only required if custom port is required (i.e. local)
}

# Registration Simulation
test_registration_p1 = {"role": "guest"}    # For test_participant_1
test_registration_p2 = {"role": "host"}     # For test_participant_2

# Tag Simulation
test_tags_p1 = {    # For test_participant_1 
    "train": [["iid_1"], ["non_iid_1"]],
    "evaluate": [["edge_test_missing_coecerable_vals"]]
}

test_tags_p2 = {    # For test_participant_2
    "train": [["iid_2"], ["non_iid_2"]]
}

###################
# Helper Function #
###################

def execute_post(url, payload):
    status = requests.post(url=url, json=payload)
    assert status.status_code in [200, 201]
    return status.json()

##########
# Script #
##########

if __name__ == "__main__":
    # Step 1: TTP registers a new project
    project_resp = execute_post(url=project_upload_url, payload=test_project)
    logging.debug(f"New project: {project_resp}")
    
    # Step 2: TTP registers an experiment
    expt_resp = execute_post(url=expt_upload_url, payload=test_experiment)
    logging.debug(f"New experiment: {expt_resp}")

    # Step 3: TTP registers a run
    run_resp = execute_post(url=run_upload_url, payload=test_run)
    logging.debug(f"New run: {run_resp}")

    # Step 4: Participants register server connection information on TTP node
    participant_1_resp = execute_post(
        url=participant_upload_url, 
        payload=test_participant_1
    )
    logging.debug(f"New participant 1: {participant_1_resp}")

    participant_2_resp = execute_post(
        url=participant_upload_url, 
        payload=test_participant_2
    )
    logging.debug(f"New participant 2: {participant_2_resp}")

    # Step 5: Participants register to partake in aforementioned project
    registration_1_resp = execute_post(
        url=registration_1_url, 
        payload=test_registration_p1
    )
    logging.debug(f"New registration for participant 1: {registration_1_resp}")

    registration_2_resp = execute_post(
        url=registration_2_url, 
        payload=test_registration_p2
    )
    logging.debug(f"New registration for participant 2: {registration_2_resp}")


    # Step 6: Participants register data tags to be used in project
    tags_1_resp = execute_post(url=tags_1_url, payload=test_tags_p1)
    logging.debug(f"New tags registered for participant 1: {tags_1_resp}")

    tags_2_resp = execute_post(url=tags_2_url, payload=test_tags_p2)
    logging.debug(f"New tags registered for participant 2: {tags_2_resp}")
