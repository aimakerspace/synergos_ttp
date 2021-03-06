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
expt_id_1 = "test_experiment_1" # 1st expt declared to test out default functions
expt_id_2 = "test_experiment_2" # 2nd expt to test for expt-level bulk testing
run_id_1 = "test_run_1" # 1nd run to test for run-level bulk testing (linked to "test_experiment_1")
run_id_2 = "test_run_2" # 2nd run to test for run-level bulk testing (linked to "test_experiment_2")
run_id_3 = "test_run_3" # 3nd run to test for run-level bulk testing (linked to "test_experiment_2")

# Relevant Connection Endpoints
ttp_host = "0.0.0.0"#"localhost"
ttp_port = 5000#15000
base_ttp_connect_url = f"http://{ttp_host}:{ttp_port}/ttp/connect"

project_upload_url = f"{base_ttp_connect_url}/projects"
project_retrieval_url = f"{base_ttp_connect_url}/projects/{project_id}"

expt_upload_url = f"{project_retrieval_url}/experiments"
expt_retrieval_url_1 = f"{project_retrieval_url}/experiments/{expt_id_1}"
expt_retrieval_url_2 = f"{project_retrieval_url}/experiments/{expt_id_2}"

run_upload_url_1 = f"{expt_retrieval_url_1}/runs"
run_upload_url_2 = f"{expt_retrieval_url_2}/runs"
run_retrieval_url_1 = f"{expt_retrieval_url_1}/runs/{run_id_1}"
run_retrieval_url_2 = f"{expt_retrieval_url_2}/runs/{run_id_2}"
run_retrieval_url_3 = f"{expt_retrieval_url_2}/runs/{run_id_3}"

# Relevant Training Endpoints
base_ttp_train_url = f"http://{ttp_host}:{ttp_port}/ttp/train"
project_train_url = f"{base_ttp_train_url}/projects/{project_id}"

alignment_init_url = f"{project_train_url}/alignments"
model_init_url = f"{project_train_url}/models/{expt_id_1}/{run_id_1}"
optim_init_url = f"{project_train_url}/models/{expt_id_1}/optimizations"

# Relevant Evaluation Endpoints
base_ttp_eval_url = f"http://{ttp_host}:{ttp_port}/ttp/evaluate"
validation_init_url = f"{base_ttp_eval_url}/projects/{project_id}/validations"
prediction_init_url = f"{base_ttp_eval_url}/participants/test_participant_1/predictions"

# Project Simulation
test_project = {
    "project_id": project_id,
    "action": "classify",
    "incentives": {
        "tier_1": ["test_worker_1"],
        "tier_2": ["test_worker_2"]
    }
}

# Experiment Simulation
test_experiment_1 = {
    "expt_id": expt_id_1,
    "model": [
        {
            "activation": "sigmoid",
            "is_input": True,
            "l_type": "Linear",
            "structure": {
                "bias": True,
                "in_features": 15, #28,
                "out_features": 1
            }
        }
    ]
}

test_experiment_2 = {
    "expt_id": expt_id_2,
    "model": [
        {
            "activation": "sigmoid",
            "is_input": True,
            "l_type": "Linear",
            "structure": {
                "bias": True,
                "in_features": 15,
                "out_features": 10
            }
        },
        {
            "activation": "sigmoid",
            "is_input": True,
            "l_type": "Linear",
            "structure": {
                "bias": True,
                "in_features": 10,
                "out_features": 90
            }
        },
        {
            "activation": "sigmoid",
            "is_input": True,
            "l_type": "Linear",
            "structure": {
                "bias": True,
                "in_features": 90,
                "out_features": 80
            }
        },
        {
            "activation": "sigmoid",
            "is_input": True,
            "l_type": "Linear",
            "structure": {
                "bias": True,
                "in_features": 80,
                "out_features": 70
            }
        },
        {
            "activation": "sigmoid",
            "is_input": True,
            "l_type": "Linear",
            "structure": {
                "bias": True,
                "in_features": 70,
                "out_features": 60
            }
        },
        {
            "activation": "sigmoid",
            "is_input": True,
            "l_type": "Linear",
            "structure": {
                "bias": True,
                "in_features": 60,
                "out_features": 50
            }
        },
        {
            "activation": "sigmoid",
            "is_input": True,
            "l_type": "Linear",
            "structure": {
                "bias": True,
                "in_features": 50,
                "out_features": 40
            }
        },
        {
            "activation": "sigmoid",
            "is_input": True,
            "l_type": "Linear",
            "structure": {
                "bias": True,
                "in_features": 40,
                "out_features": 30
            }
        },
        {
            "activation": "sigmoid",
            "is_input": True,
            "l_type": "Linear",
            "structure": {
                "bias": True,
                "in_features": 30,
                "out_features": 20
            }
        },
        {
            "activation": "sigmoid",
            "is_input": True,
            "l_type": "Linear",
            "structure": {
                "bias": True,
                "in_features": 20,
                "out_features": 10
            }
        },
        {
            "activation": "sigmoid",
            "is_input": True,
            "l_type": "Linear",
            "structure": {
                "bias": True,
                "in_features": 10,
                "out_features": 1
            }
        }
    ]
}

# Run Simulation
test_run_1 = {
    "run_id": run_id_1,
    "algorithm": "FedProx",
    "batch_size": 32,
    "rounds": 2,
    "epochs": 1,
    "lr": 0.15,
    "weight_decay": 0.01,
    "mu": 0.4,
    "l1_lambda": 0.01,
    "l2_lambda": 0.01,
    "base_lr": 0.001, 
    "max_lr": 0.1
}

test_run_2 = {
    "run_id": run_id_2,
    "algorithm": "FedProx",
    "batch_size": 32,
    "rounds": 2,
    "epochs": 1,
    "lr": 0.2,
    "weight_decay": 0.02,
    "mu": 0.15,
    "l1_lambda": 0.2,
    "l2_lambda": 0.3,
    "patience": 2,
    "delta": 0.0001,
    "base_lr": 0.001, 
    "max_lr": 0.1
}

test_run_3 = {
    "run_id": run_id_3,
    "algorithm": "FedProx",
    "batch_size": 32,
    "rounds": 1,
    "epochs": 1,
    "lr": 0.3,
    "weight_decay": 0.03,
    "mu": 0.2,
    "l1_lambda": 0.2,
    "l2_lambda": 0.3,
    "base_lr": 0.001, 
    "max_lr": 0.1
}

# 20-party participant Simulation
# Notes: 
# - 'participant_id' declared should be the same as 'id'
# - Either specify docker bridge IP (i.e. standalone) or server IP
# - Either specify docker bridge port (i.e. standalone) or server port
participant_count = 2
participants = {}
for p_idx in range(1, participant_count+1): 

    participant_id = f"test_participant_{p_idx}"
    host_ip = f"172.17.0.{p_idx + 1}"
    participant_payload = {
        "id": participant_id,
        "host": host_ip,
        "port": 8020,
        "log_msgs": False,
        "verbose": False,
        "f_port": 5000  
    }

    registration_payload = {"role": "guest"}

    tags_payload = (
        { 
            "train": [
                #["iid_1"], 
                ["non_iid_1"]
                # ["edge_test_misalign"]
                # ["edge_test_na_slices"]
            ],
            "evaluate": [["edge_test_missing_coecerable_vals"]]
        } 
        if (p_idx % 2) == 1 else 
        {
            "train": [
                #["iid_2"], 
                ["non_iid_2"]
            ]
        }
    )

    # tags_payload = (
    #     { 
    #         "train": [["train"]],
    #         "evaluate": [["evaluate"]]
    #     }
    # )

    metadata = {
        'participant': participant_payload,
        'registration': registration_payload,
        'tags': tags_payload
    }
    participants[participant_id] = metadata

# Model initialisation/validation simulation
init_params = {
    "dockerised": True,
    "verbose": True,
    "log_msgs": True
}

tuning_params = {
    'search_space': {
        "batch_size": {"_type":"choice", "_value": [16, 32, 64, 128]},
        "hidden_size":{"_type":"choice","_value":[128, 256, 512, 1024]},
        "lr":{"_type":"choice","_value":[0.0001, 0.001, 0.01, 0.1]},
        "momentum":{"_type":"uniform","_value":[0, 1]}
    },
    'tuner': "TPE",
    'metric': "accuracy",
    'optimize_mode': "maximize",
    'trial_concurrency': 1,
    'max_exec_duration': "1h",
    'max_trial_num': 10,
    'is_remote': True,
    'use_annotation': True,
    'dockerised': True,
    'verbose': True,
    'log_msgs': True
}

# # Inference initialisation simulation
# infer_params = {
#     "dockerised": True,
#     "tags": {
#         "test_project": [["iid_1"]]
#     }
# }

infer_params = {
    "dockerised": True,
    "tags": {
        "test_project": [["predict"]]
    }
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

    ##############
    # Connection #
    ##############

    # Step 1: TTP registers a new project
    project_resp = execute_post(url=project_upload_url, payload=test_project)
    logging.debug(f"New project: {project_resp}")
    
    # Step 2: TTP registers 2 experiments
    expt_resp_1 = execute_post(url=expt_upload_url, payload=test_experiment_1)
    logging.debug(f"New experiment set 1: {expt_resp_1}")

    expt_resp_2 = execute_post(url=expt_upload_url, payload=test_experiment_2)
    logging.debug(f"New experiment set 2: {expt_resp_2}")

    # Step 3: TTP registers a run
    run_resp_1 = execute_post(url=run_upload_url_1, payload=test_run_1)
    logging.debug(f"New run: {run_resp_1}")

    run_resp_2 = execute_post(url=run_upload_url_2, payload=test_run_2)
    logging.debug(f"New run: {run_resp_2}")

    run_resp_3 = execute_post(url=run_upload_url_2, payload=test_run_3)
    logging.debug(f"New run: {run_resp_3}")

    for p_idx, (participant_id, metadata) in enumerate(participants.items()):

        participant_upload_url = f"{base_ttp_connect_url}/participants"
        participant_retrieval_url = f"{base_ttp_connect_url}/participants/{participant_id}"
        registration_url = f"{participant_retrieval_url}/projects/{project_id}/registration"
        tags_url = f"{registration_url}/tags"

        # Step 4: Participants register server connection information on TTP node
        participant_resp = execute_post(
            url=participant_upload_url, 
            payload=metadata['participant']
        )
        logging.debug(f"New participant: {participant_resp}")

        # Step 5: Participants register to partake in aforementioned project
        registration_resp = execute_post(
            url=registration_url, 
            payload=metadata['registration']
        )
        logging.debug(f"New registration for participant: {registration_resp}")

        # Step 6: Participants register data tags to be used in project
        tags_resp = execute_post(url=tags_url, payload=metadata['tags'])
        logging.debug(f"New tags registered for participant: {tags_resp}")

    ############
    # Training #
    ############

    # Step 1: TTP intialises multiple feature alignment
    align_resp = execute_post(url=alignment_init_url, payload=None)
    logging.debug(f"New alignments: {align_resp}")

    # Step 2: TTP commences model training for specified experiment-run set
    model_resp = execute_post(url=model_init_url, payload=init_params)
    logging.debug(f"New model: {model_resp}")

    # Step 3: TTP commences hyperparameter tuning for specified model
    optim_resp = execute_post(url=optim_init_url, payload=tuning_params)
    logging.debug(f"New optimization set: {optim_resp}")

    ##############
    # Evaluation #
    ##############

    # # Step 1: TTP commences post-mortem model validation
    # val_resp = execute_post(url=validation_init_url, payload=init_params)
    # logging.debug(f"New prediction: {val_resp}")

    # # Step 2: Participant requests trained global models from TTP for inference
    # predict_resp = execute_post(url=prediction_init_url, payload=infer_params)
    # logging.debug(f"New prediction: {predict_resp}")
