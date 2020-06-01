#!/usr/bin/env python

####################
# Required Modules #
####################

# Generic/Built-in
import argparse
import asyncio
import concurrent.futures
import logging
import multiprocessing as mp
import os
import time
from glob import glob
from pathlib import Path

# Libs
import dill
import syft as sy
import torch as th
from pathos.multiprocessing import ProcessingPool
from syft.workers.websocket_client import WebsocketClientWorker

# Custom
from rest_rpc import app
from rest_rpc.training.core.arguments import Arguments
from rest_rpc.training.core.model import Model
from rest_rpc.training.core.federated_learning import FederatedLearning
from rest_rpc.training.core.utils import Governor, RPCFormatter

##################
# Configurations #
##################

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

out_dir = app.config['OUT_DIR']

cache = mp.Queue()#app.config['CACHE']

rpc_formatter = RPCFormatter()

# Instantiate a local hook for coordinating clients
# Note: `is_client=True` ensures that all objects are deleted once WS connection
#       is closed. That way, there is no need to explicitly clear objects in all
#       workers, which may prematurely break PointerTensors
grid_hook = sy.TorchHook(th)

"""
[Redacted - Multiprocessing]

core_count = mp.cpu_count()

# Configure dill to recursively serialise dependencies
dill.settings['recurse'] = True

[Redacted - Asynchronised FL Grid Training]
"""
# Configure timeout settings for WebsocketClientWorker
sy.workers.websocket_client.TIMEOUT_INTERVAL = 3600

#sy.workers.websocket_client.websocket.enableTrace(True)
REF_WORKER = sy.local_worker


#############
# Functions #
#############

def connect_to_ttp(log_msgs=False, verbose=False):
    """ Creates coordinating TTP on the local machine, and makes it the point of
        reference for subsequent federated operations. Since this implementation
        is that of the master-slave paradigm, the local machine would be
        considered as the subject node in the network, allowing the TTP to be
        represented by a VirtualWorker.

        (While it is possible for TTP to be a WebsocketClientWorker, it would 
        make little sense to route messages via a WS connection to itself, since
        that would add unnecessary network overhead.)
    
    Returns:
        ttp (sy.VirtualWorker)
    """
    # Create a virtual worker representing the TTP
    ttp = sy.VirtualWorker(
        hook=grid_hook, 
        id='ttp',
        is_client_worker=False,
        log_msgs=log_msgs,
        verbose=verbose    
    )

    # Replace point of reference within federated hook with TTP
    sy.local_worker = ttp
    grid_hook.local_worker = ttp
    assert (ttp is grid_hook.local_worker)
    assert (ttp is sy.local_worker)

    logging.debug(f"Local worker w.r.t grid hook: {grid_hook.local_worker}")
    logging.debug(f"Local worker w.r.t env      : {sy.local_worker}")

    return grid_hook.local_worker


def connect_to_workers(keys, reg_records, dockerised=True, log_msgs=False, verbose=False):
    """ Create client workers for participants to their complete WS connections
        Note: At any point of time, there will always be 1 set of workers per
              main process

    Args:
        keys (dict(str)): Processing IDs for caching
        reg_records (list(tinydb.database.Document))): Registry of participants
        log_msgs (bool): Toggles if messages are to be logged
        verbose (bool): Toggles verbosity of logs for WSCW objects
    Returns:
        workers (list(WebsocketClientWorker))
    """
    workers = []
    for reg_record in reg_records:

        # Remove redundant fields
        config = rpc_formatter.strip_keys(reg_record['participant'])
        config.pop('f_port')

        # Replace log & verbosity settings with locally specified settings
        config['log_msgs'] = log_msgs
        config['verbose'] = verbose

        curr_worker = WebsocketClientWorker(
            hook=grid_hook,

            # When False, PySyft manages object clean up. Here, this is done on
            # purpose, since there is no need to propagate gradient tracking
            # tensors back to the worker node. This ensures that the grid is
            # self-contained at the TTP, and that the workers' local grid is not
            # polluted with unncessary tensors. Doing so optimizes tag searches.
            is_client_worker=False, 

            **config
        )
        workers.append(curr_worker)

    logging.debug(f"Participants: {[w.id for w in workers]}")

    return workers


def terminate_connections(ttp, workers):
    """ Terminates the WS connections between remote WebsocketServerWorkers &
        local WebsocketClientWorkers
        Note: Objects do not need to be explicitly cleared since garbage
              collection should kick in by default. Any problems arising from
              this is a sign that something is architecturally wrong with the
              current implementation and should not be silenced.

    Args:
        _id (dict(str)): Processing IDs for caching
    """  
    # Ensure that the grid has it original reference restored. This should
    # destroy all grid references to TTP's VirtualWorker, which is necessary for 
    # it to be successfully deleted
    grid_hook.local_worker = REF_WORKER
    sy.local_worker = REF_WORKER

    # Finally destroy TTP
    ttp.remove_worker_from_local_worker_registry()
    del ttp

    try:
        logging.error(f"{ttp} has not been deleted!")
    except NameError:
        logging.info(f"TTP has been successfully deleted!")

    for w_idx, worker in enumerate(workers):

        # Superclass of websocketclient (baseworker) contains a worker registry 
        # which caches the websocketclient objects when the auto_add variable is
        # set to True. This registry is indexed by the websocketclient ID and 
        # thus, recreation of the websocketclient object will not get replaced 
        # in the registry if the ID is the same. If obj is not removed from
        # local registry before the WS connection is closed, this will cause a 
        # `websocket._exceptions.WebSocketConnectionClosedException: socket is 
        # already closed.` error since it is still referencing to the previous 
        # websocketclient connection that was closed. The solution 
        # was to simply call the remove_worker_from_local_worker_registry() 
        # method on the websocketclient object before closing its connection.
        worker.remove_worker_from_local_worker_registry()
        del worker

        try:
            logging.error(f"{worker} has not been deleted!")
        except NameError:
            logging.info(f"Worker_{w_idx} has been successfully deleted")


def load_selected_run(run_record):
    """ Load in specified federated experimental parameters to be conducted from
        a registered configuration set

    Args:
        run_record (dict): Hyperparameters defining the FL training environment
    Returns:
        FL Training run arguments (Arguments)
    """
    # Remove redundant fields & initialise arguments
    run_params = rpc_formatter.strip_keys(run_record)#, concise=True)
    args = Arguments(**run_params)

    return args


def load_selected_experiment(expt_record):
    """ Load in specified federated model architectures to be used for training
        from configuration files

    Args:
        expt_record (dict): Structural template of model to be initialise
    Returns:
        Model to be used in FL training (Model)
    """
    # Remove redundant fields & initialise Model
    structure = rpc_formatter.strip_keys(expt_record)['model']#, concise=True)
    model = Model(structure)

    return model


def load_selected_runs(fl_params):
    """ Load in specified federated experimental parameters to be conducted from
        configuration files

    Args:
        fl_params (dict): Experiment Ids of experiments to be run
    Returns:
        runs (dict(str,Arguments))
    """
    runs = {run_id: Arguments(**params) for run_id, params in fl_params.items()}

    logging.debug(f"Runs loaded: {runs.keys()}")

    return runs


def load_selected_models(model_params):
    """ Load in specified federated model architectures to be used for training
        from configuration files

    Args:
        model_params (dict): Specified models to be trained
    Returns:
        models (dict(str,Model))
    """
    models = {name: Model(structure) for name, structure in model_params.items()}

    logging.debug(f"Models loaded: {models.keys()}")

    return models


def start_expt_run_training(keys: dict, registrations: list, 
                            experiment: dict, run: dict, 
                            dockerised: bool, log_msgs: bool, verbose: bool):
    """ Trains a model corresponding to a SINGLE experiment-run combination

    Args:
        keys (dict): Relevant Project ID, Expt ID & Run ID
        ttp (sy.VirtualWorker): Allocated trusted third party in the FL grid
        workers (list(WebsocketClientWorker)): All WSCWs for each participant
        experiment (dict): Parameters for reconstructing experimental model
        run (dict): Hyperparameters to be used during grid FL training
    Returns:
        Path-to-trained-models (dict(str))
    """

    def train_combination():

        logging.debug(f"Before Initialisation - Reference Worker            : {REF_WORKER}")
        logging.debug(f"Before Initialisation - Local worker w.r.t grid hook: {grid_hook.local_worker}")
        logging.debug(f"Before Initialisation - Local worker w.r.t env      : {sy.local_worker}")

        # Create worker representation for local machine as TTP
        ttp = connect_to_ttp(log_msgs=log_msgs, verbose=verbose)

        logging.debug(f"After Initialisation - Reference Worker            : {REF_WORKER}")
        logging.debug(f"After Initialisation - Local worker w.r.t grid hook: {grid_hook.local_worker}")
        logging.debug(f"After Initialisation - Local worker w.r.t env      : {sy.local_worker}")

        # Complete WS handshake with participants
        workers = connect_to_workers(
            keys=keys,
            reg_records=registrations,
            dockerised=dockerised,
            log_msgs=log_msgs,
            verbose=verbose
        )

        logging.debug(f"Before training - Reference worker: {REF_WORKER}")
        logging.debug(f"Before training - Registered workers in grid: {grid_hook.local_worker._known_workers}")
        logging.debug(f"Before training - Registered workers in env : {sy.local_worker._known_workers}")

        model = load_selected_experiment(expt_record=experiment)
        args = load_selected_run(run_record=run)
    
        # Perform a Federated Learning experiment
        fl_expt = FederatedLearning(args, ttp, workers, model)
        fl_expt.load()
        fl_expt.fit()

        # Export trained model weights/biases for persistence
        res_dir = os.path.join(
            out_dir, 
            keys['project_id'], 
            keys['expt_id'], 
            keys['run_id']
        )
        Path(res_dir).mkdir(parents=True, exist_ok=True)

        out_paths = fl_expt.export(res_dir)

        logging.info(f"Final model: {fl_expt.global_model.state_dict()}")
        logging.info(f"Final model stored at {out_paths}")
        logging.info(f"Loss history: {fl_expt.loss_history}")

        logging.debug(f"After training - Reference worker: {REF_WORKER}")
        logging.debug(f"After training - Registered workers in grid: {grid_hook.local_worker._known_workers}")
        logging.debug(f"After training - Registered workers in env : {sy.local_worker._known_workers}")

        # Close WSCW local objects once training process is completed (if possible)
        # (i.e. graceful termination)
        terminate_connections(ttp=ttp, workers=workers)

        logging.debug(f"After termination - Reference worker: {REF_WORKER}")
        logging.debug(f"After termination - Registered workers in grid: {grid_hook.local_worker._known_workers}")
        logging.debug(f"After termination - Registered workers in env : {sy.local_worker._known_workers}")
        
        return out_paths

    logging.info(f"Current combination: {keys}")

    # Send initialisation signal to all remote worker WSSW objects
    governor = Governor(dockerised=dockerised, **keys)
    governor.initialise(reg_records=registrations)

    try:
        results = train_combination()

        def magic_method(obj):
            import inspect
            frame = inspect.currentframe()
            try:
                names = [name for name, val in frame.f_back.f_locals.items() if val is obj]
                names += [name for name, val in frame.f_back.f_globals.items()
                        if val is obj and name not in names]
                return names
            finally:
                del frame

        from syft.generic.pointers.object_pointer import ObjectPointer
        logging.debug(f"All remaining ObjectPointers un-collected: {magic_method(ObjectPointer)}")

        logging.info(f"Objects left in env: {sy.local_worker._objects}, {sy.local_worker._known_workers}")
    except OSError:
        print("Caught this OS problem...")

    # Send terminate signal to all participants' worker nodes
    governor = Governor(dockerised=dockerised, **keys)
    governor.terminate(reg_records=registrations)

    return results


# async def train_on_combinations(combinations):
#     """ Asynchroneous function to perform FL grid training over all registered
#         participants over a series of experiment-run combinations

#     Args:
#         combinations (dict(tuple, dict)): All TTP registered combinations
#     Returns:
#         Results of FL grid training from enumerated combinations (dict)
#     """
#     # Apply asynchronous training to each batch
#     futures = [
#         start_expt_run_training(kwargs) 
#         for kwargs in combinations.values()
#     ]
#     all_outpaths = await asyncio.gather(*futures)

#     results = dict(zip(combinations.keys(), all_outpaths))
#     return results


def start_proc(kwargs):
    """ Automates the execution of Federated learning experiments on different
        hyperparameter sets & model architectures

    Args:
        kwargs (dict): Experiments & models to be tested
    Returns:
        Path-to-trained-models (list(str))
    """
    experiments = kwargs['experiments']
    runs = kwargs['runs']
    registrations = kwargs['registrations']
    is_verbose = kwargs['verbose']
    log_msgs = kwargs['log_msgs']
    is_dockerised = kwargs['dockerised']

    training_combinations = {}
    for expt_record in experiments:
        curr_expt_id = expt_record['key']['expt_id']

        for run_record in runs:
            run_key = run_record['key']
            r_project_id = run_key['project_id']
            r_expt_id = run_key['expt_id']
            r_run_id = run_key['run_id']

            if r_expt_id == curr_expt_id:

                combination_key = (r_project_id, r_expt_id, r_run_id)
                project_expt_run_params = {
                    'keys': run_key,
                    'registrations': registrations,
                    'experiment': expt_record,
                    'run': run_record,
                    'dockerised': is_dockerised, 
                    'log_msgs': log_msgs, 
                    'verbose': is_verbose
                }
                training_combinations[combination_key] = project_expt_run_params

    logging.info(f"{training_combinations}")

    # """
    # ##########################################################
    # # Multiprocessing - Run each process on an isolated core #
    # ##########################################################
    # [Redacted - Due to PySyft objects being unserialisable, this feature has
    #             been frozen until further notice
    # ]

    # pool = ProcessingPool(nodes=core_count)

    # results = pool.amap(start_expt_run_training, training_combinations.values())

    # while not results.ready():
    #     time.sleep(1)
        
    # results = results.get()

    # # Clean up Pathos multiprocessing pool
    # pool.close()
    # pool.join()
    # pool.terminate()

    # completed_trainings = dict(zip(training_combinations.keys(), results))
    # return completed_trainings
    # """

    # """
    # #############################################################
    # # Optimisation Alternative - Asynchronised FL grid Training #
    # #############################################################
    # [Redacted - Due to _recv stuck listening in a circular loop, this feature 
    #             has been frozen until further notice
    # ]

    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)

    # try:
    #     completed_trainings = loop.run_until_complete(
    #         train_on_combinations(combinations=training_combinations)
    #     )
    # finally:
    #     loop.close()

    # return completed_trainings
    # """
    
    # #######################################################################
    # # Default Implementation - Synchroneous execution of FL grid training #
    # #######################################################################

    # # results = map(
    # #     lambda kwargs: start_expt_run_training(**kwargs), 
    # #     training_combinations.values()
    # # )

    completed_trainings = {
        combination_key: start_expt_run_training(**kwargs) 
        for combination_key, kwargs in training_combinations.items()
    }

    return completed_trainings

##########
# Script #
##########

if __name__ == "__main__":
    
    """
    parser = argparse.ArgumentParser(
        description="Run a Federated Learning experiment."
    )

    parser.add_argument(
        "--models",
        "-m",
        type=str, 
        nargs="+",
        required=True,
        help="Model architecture to load"
    )

    parser.add_argument(
        "--experiments",
        "-e",
        type=str, 
        nargs="+",
        required=True,
        help="Port number of the websocket server worker, e.g. --port 8020"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="if set, websocket client worker will be started in verbose mode"
    )

    kwargs = vars(parser.parse_args())
    logging.debug(f"TTP Parameters: {kwargs}")

    start_proc(kwargs)
    """

