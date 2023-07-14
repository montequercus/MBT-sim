import numpy as np
import os

from altwalker.planner import OnlinePlanner
from altwalker.executor import PythonExecutor, create_executor
from altwalker.reporter import FileReporter, ClickReporter
from altwalker.walker import Walker
from altwalker.graphwalker import GraphWalkerClient, GraphWalkerService

"""
Run the test package on the TwoWaySwitch ABM model.
This test execution script simply runs the test once. No replications are implemented.
"""

## Planner: plans next step for Executor
current_directory = os.getcwd()
model_path_rel = 'models\TwoWay_process.json'
model_path_abs = os.path.join(current_directory, model_path_rel)

stop_condition = "random(vertex_coverage(100))" # All vertices of 'process graph' must be passed.
model_specification = [(model_path_abs, stop_condition)]

np.random.seed()
gw_port = np.random.randint(5000, 10000)
gw_client = GraphWalkerClient(host='127.0.0.1', verbose=False, port=gw_port)
gw_service = GraphWalkerService(models=model_specification, port=gw_port)
planner = OnlinePlanner(client=gw_client, service=gw_service)

## Executor
test_path = "tests"
url = "http://localhost:5000" # Not to be confused with 'gw_port'
executor = create_executor(path=test_path, executor_type="python", url=url)

## Reporter
reporter = ClickReporter()

## Walker: Coordinates execution of a test
walker = Walker(planner, executor, reporter)
walker.run() # Run a test using the graph


