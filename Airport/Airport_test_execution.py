import os
import random
import time

from altwalker.planner import OnlinePlanner
from altwalker.executor import PythonExecutor, create_executor, HttpExecutor, create_python_executor, create_http_executor
from altwalker.reporter import FileReporter, ClickReporter, Reporter, Reporting
from altwalker.walker import Walker
from altwalker.graphwalker import GraphWalkerClient, GraphWalkerService

current_directory = os.getcwd()
model_path_rel = 'models\Components.json'
model_path_abs = os.path.join(current_directory, model_path_rel)

## Initialie AltWalker API objects
stop_condition = "weighted_random(requirement_coverage(100))"
port = 6000
gw_client = GraphWalkerClient(host='127.0.0.1', verbose=False, port=port)
gw_service = GraphWalkerService(models=[(model_path_abs, stop_condition)], port=port)

planner = OnlinePlanner(client=gw_client, service=gw_service)
executor = create_executor(path="tests", executor_type='python', url="http://localhost:5000")

bool_print_paths = True
reporter_standard = ClickReporter() if bool_print_paths else Reporter()
reporter_to_file = FileReporter('output.txt')
reporter = Reporting()  # Combines multiple reporters
reporter.register("standard", reporter_standard)
reporter.register("to file", reporter_to_file)

walker = Walker(planner, executor, reporter)

## Define properties of servers that can be tested
passport_check = {
    'server_name': 'Passport check',
    'service_time_min': 30,
    'service_time_max': 90
}

luggage_placing = {
    'server_name': 'Luggage placing',
    'service_time_min': 20,
    'service_time_max': 40
}

## Define experiment
t_end = 10000 # Simulation end time
seed_SUT = 77 # Seed used by SUT
server_under_test = passport_check # SELECT SERVER TO BE TESTED
show_messages = False # Show messages from SUT

## Set experimental setup in SUT via graph
planner.set_data('bool_from_CLI', False) # Indicate that initial values are set by test execution script
planner.set_data('seed', seed_SUT)
planner.set_data('t_end', t_end)
planner.set_data('component_name', server_under_test['server_name'])
planner.set_data('service_time_min', server_under_test['service_time_min'])
planner.set_data('service_time_max', server_under_test['service_time_max'])
planner.set_data('show_messages', show_messages)

## Run test model, then end Java process
walker.run()
gw_service.kill()

