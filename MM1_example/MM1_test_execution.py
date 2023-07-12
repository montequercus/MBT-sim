import unittest
import numpy as np
import sys
import os
import json # For writing SUT parameter values to a file
import random
import salabim

from altwalker.planner import OnlinePlanner
from altwalker.executor import PythonExecutor, create_executor
from altwalker.reporter import FileReporter, ClickReporter
from altwalker.walker import Walker
from altwalker.graphwalker import GraphWalkerClient, GraphWalkerService

## Settings for SUT and test script
num_replications = 2
num_elements = 500 # Number of elements passed in graph for each replication
iat = 10
server_time = 5

# Check if json file has to be made
if not os.path.exists('SUT_settings.json'):
    with open('SUT_settings.json', 'w') as f:
        json.dump({}, f) # Save an empty json string

## Settings for Planner: "determine the next step executed by the Executor"
current_directory = os.getcwd()
model_path_rel = 'models\MM1_FIFO.json'
model_path_abs = os.path.join(current_directory, model_path_rel)

stop_condition = f"random(length({num_elements}))"

model_spec = [(model_path_abs, stop_condition)] # Model specification as list

## Make list of SUT seeds for replications
random.seed(100)
seeds_used = [random.randint(0,1234567) for i in range(num_replications)]

## Run test script for each replication
for rep in range(num_replications):
    ## Save paramater values for SUT instance
    params = {'rep_num': rep,
              'seed': seeds_used[rep],
              'iat': iat,
              'server_time': server_time}
    print(params)
    with open('SUT_settings.json', 'w') as f:
        json.dump(params, f)

    ## Planner
    np.random.seed()
    gw_port = np.random.randint(5000, 10000)  # Select random port number to prevent GraphWalker errors
    print(gw_port)
    # gw_port = 7000
    gw_client = GraphWalkerClient(host='127.0.0.1', verbose=False, port=gw_port)
    gw_service = GraphWalkerService(models=model_spec, port=gw_port)

    planner = OnlinePlanner(client=gw_client, service=gw_service)
    print(planner)

    ## Executor
    test_path = "tests"
    url = "http://localhost:5000"
    executor = create_executor(path=test_path, executor_type="python", url=url)

    ## Reporter
    reporter = ClickReporter()

    ## Walker: Coordinates execution of a test
    walker = Walker(planner, executor, reporter)
    walker.run() # Run a test