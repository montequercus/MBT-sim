import numpy as np
import os
import random
import time # For getting the execution time
import pandas as pd

from altwalker.planner import OnlinePlanner
from altwalker.executor import PythonExecutor, create_executor, HttpExecutor, create_python_executor, create_http_executor
from altwalker.reporter import FileReporter, ClickReporter, Reporter, Reporting
from altwalker.walker import Walker
from altwalker.graphwalker import GraphWalkerClient, GraphWalkerService

## Get paths
current_directory = os.getcwd()
model_path_rel = 'models\MM1_FIFO_with_s_and_fail.json'
model_path_abs = os.path.join(current_directory, model_path_rel)

## Initialize AltWalker API objects
def create_AltWalker_run(port, model_path_abs, stop_condition, bool_print_paths):
    gw_client = GraphWalkerClient(host='127.0.0.1', verbose=False, port=port)
    gw_service = GraphWalkerService(models=[(model_path_abs, stop_condition)], port=port)

    planner = OnlinePlanner(client=gw_client, service=gw_service)
    executor = create_executor(path="tests", executor_type='python', url="http://localhost:5000")

    reporter_standard = ClickReporter() if bool_print_paths else Reporter()
    reporter_to_file = FileReporter('output.txt')
    reporter = Reporting()  # Combines multiple reporters
    reporter.register("standard", reporter_standard)
    reporter.register("to file", reporter_to_file)

    walker = Walker(planner, executor, reporter)

    return gw_service, gw_client, planner, executor, reporter, walker

## Define experiments
bool_print_paths = True # True: AltWalker ClickReporter will print all generated steps to stdout
port = 6000
stop_condition = "weighted_random(requirement_coverage(100) or length(100000))"

t_end = 100 # SUT simulated time to end test at
random.seed(100) # Initialize RNG
seed = 77 # Set a seed for SUT (Salabim)

# Input parameters for experiments
iat = 1.0
server_time = 0.2

start_time = time.time() # To calculate execution time

## Run experiments
port += 1 # New port number for GraphWalker service
gw_service, gw_client, planner, executor, reporter, walker = \
    create_AltWalker_run(port, model_path_abs, stop_condition, bool_print_paths)

## Set seed and experimental set-up via graph
planner.set_data('seed', seed)
planner.set_data('t_end', t_end)

planner.set_data('iat', iat)
planner.set_data('server_time', server_time)

## Print parameters for this run
print(f"One experiment with iat = {iat} and server time = {server_time}, for {t_end} seconds.")

## Run and reset AltWalker
walker.run()
output_data = planner.get_data() # Get graph variables at end of run
gw_service.kill() # End associated Java process


## Get execution time
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Execution time: {elapsed_time:.2f}")
