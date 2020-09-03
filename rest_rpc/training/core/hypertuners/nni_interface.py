#!/usr/bin/env python

####################
# Required Modules #
####################

# Generic/Built-in
import json
import logging
import os
import shlex
import subprocess
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Tuple, Union

# Libs
import psutil
import yaml

# Custom
from rest_rpc import app
from rest_rpc.training.core.hypertuners.abstract import AbstractTuner

##################
# Configurations #
##################

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

src_dir = app.config['SRC_DIR']
cores_used = app.config['CORES_USED']
gpu_count = app.config['GPU_COUNT']

##############################################
# Hyperparameter Tuning Interface - NNITuner #
##############################################

class NNITuner(AbstractTuner):
    """
    Interfacing class for performing hyperparameter tuning on NNI.
    
    Attributes:
        platform (str): What hyperparameter tuning service to use
        log_dir (str): Directory to export cached log files
    """

    def __init__(self, log_dir: str = None):
        self.log_dir = log_dir

    ###########    
    # Helpers #
    ###########

    @staticmethod
    def _execute_command(command):
        """ Executes commandline operations in Python

        Args:
            command (str): Commandline command to be executed
        Returns:
            Text outputs from executed command
        """
        completed_process = subprocess.run(
            shlex.split(command),
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        results = completed_process.stdout
        
        return results


    def _generate_search_config(
        self, 
        search_space: Dict[str, Dict[str, Union[str, bool, int, float]]]
    ):
        """ Takes in a user-defined search space for tuning a particular 
            process/function and exports it to a JSON file

        Args:
            search_space (dict): Dictionary containing ranges/options to test
                for specified hyperparameter sets compatible with the system
        Returns:
            Path to search configurations (str)
        """
        search_config_path = os.path.join(
            self.log_dir, 
            "nni", 
            "search_space.json"
        )
        with open(search_config_path, 'w') as scp:
            json.dump(search_space, scp)
        
        return search_config_path


    def _generate_tuning_config(
        self,
        project_id: str,
        expt_id: str,
        search_config_path: str,
        tuner: str,
        metric: str,
        optimize_mode: str,
        trial_concurrency: int = 1,
        max_exec_duration: str = "1h",
        max_trial_num: int = 10,
        is_remote: bool = True,
        use_annotation: bool = True
    ):
        """ Builds configuration YAML file describing current set of experiments

        Args:
            author_name (str):
            expt_name (str):
            search_config_path (str):
            tuner (str):
            optimize_mode (str):
            trial_concurrency (int):
            max_exec_duration (str):
            max_trial_num (int)
            is_remote (bool)
            use_annotation (bool)
        Returns:
            Path to tuning configuration (str)
        """
        configurations = OrderedDict()
        configurations['authorName'] = project_id
        configurations['experimentName'] = expt_id
        configurations['trialConcurrency'] = trial_concurrency
        configurations['maxExecDuration'] = max_exec_duration
        configurations['maxTrialNum'] = max_trial_num
        configurations['trainingServicePlatform'] = "remote" if is_remote else "local"
        configurations['searchSpacePath'] = search_config_path
        configurations['useAnnotation'] = use_annotation
        configurations['tuner'] = {
            'builtinTunerName': tuner,
            'classArgs': {
                'optimize_mode': optimize_mode
            }
        }

        tune_dir = os.path.join(
            src_dir, "rest_rpc", "training", "core", "hypertuners" 
        )
        driver_script_path = os.path.join(tune_dir, "nni_driver_script.py")
        configurations['trial'] = {
            'command': "python {} -pid {} -eid {} -m {} -d -l -v".format(
                driver_script_path,
                project_id,
                expt_id,
                metric
            ),
            'codeDir': tune_dir,
            'gpuNum': gpu_count,
            'cpuNum': cores_used,
            'memoryMB': psutil.virtual_memory().available # remaining system ram
        }

        nni_config_path = os.path.join(self.log_dir, "nni", "config.yaml")
        with open(nni_config_path, 'w') as ncp:
            yaml.dump(configurations, ncp)

        return nni_config_path


    def _generate_start_command(self, config_path: str) -> str:
        """
        """
        return f"nnictl create --config {config_path}"

    ##################
    # Core Functions #
    ##################

    def tune(
        self,
        project_id: str,
        expt_id: str,
        search_space: Dict[str, Dict[str, Union[str, bool, int, float]]],
        tuner: str,
        metric: str,
        optimize_mode: str,
        trial_concurrency: int = 1,
        max_exec_duration: str = "1h",
        max_trial_num: int = 10,
        is_remote: bool = True,
        use_annotation: bool = True
    ):
        """
        """
        search_config_path = self._generate_search_config(search_space)
        
        nni_config_path = self._generate_tuning_config(
            project_id=project_id,
            expt_id=expt_id,
            search_config_path=search_config_path,
            tuner=tuner,
            optimize_mode=optimize_mode,
            trial_concurrency=trial_concurrency,
            max_exec_duration=max_exec_duration,
            max_trial_num=max_trial_num,
            is_remote=is_remote,
            use_annotation=use_annotation
        )

        command = self._generate_start_command(config_path=nni_config_path)
        return self._execute_command(command)