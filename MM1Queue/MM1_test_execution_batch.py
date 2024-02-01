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
bool_print_paths = False # True: AltWalker ClickReporter will print all generated steps to stdout

port = 6000
stop_condition = "weighted_random(requirement_coverage(100) or length(100000))"

t_end = 100 # SUT simulated time to end test at
num_experiments = 1
num_replications = 2
random.seed(100) # Initialize RNG
lst_seeds = [random.randint(0, 1234567) for i in range(num_replications)]

# Accepted values for numerical tests against analytical solutions
accepted_deviation_occupancy = 3.5 # % deviaton from analytical solution for occupancy (rho)
accepted_deviation_delta_relative = 2 # % deviation from analytical solution for |(W - L/lambda)/W|
min_perc_within_bandwidth_occupancy = 50 # % of occupancy values that should be within bandwidth of analytical solution
min_perc_within_bandwidth_delta_relative = 50 # % of delta-relative values that should be within bandwidth of analytical solution

## Sample input parameters for experiments
lst_iat = np.repeat(1.0, num_experiments)
lst_server_time = np.linspace(0.2, 0.9, num_experiments)
input_data_dict = {'iat': lst_iat,
                   'server_time': lst_server_time}



## Initialize dataframe for analysis of multiple runs
outputs_for_analysis = ['t_end_exact','occupancy_mean','occupancy_verdict','delta_relative','delta_relative_verdict']
df_outputs = pd.DataFrame(columns=outputs_for_analysis)
df_settings = pd.DataFrame(columns=['experiment','replication','iat','server_time'])

start_time = time.time() # To calculate execution time

## Run experiments
for experiment in range(num_experiments):
    for replication in range(num_replications):
            port += 1 # New port number for GraphWalker service
            gw_service, gw_client, planner, executor, reporter, walker = \
                create_AltWalker_run(port, model_path_abs, stop_condition, bool_print_paths)

            ## Set seed and experimental set-up via graph
            planner.set_data('seed', lst_seeds[replication])
            planner.set_data('t_end', t_end)
            planner.set_data('d_rho', accepted_deviation_occupancy)
            planner.set_data('d_delta_relative', accepted_deviation_delta_relative)

            #if (experiment > 0) and (replication > 0):
            if not (experiment==0 and replication==0):
                num_steps = int(previous_data['n_advances'])
                print(f"Number of advances at end of previous run: {num_steps}")
                planner.set_data('n_advances', num_steps)
            else:
                planner.set_data('n_advances', 0)

            ## Set input parameters via graph
            for key, value in input_data_dict.items():
                planner.set_data(key=key, value=value[experiment])

            ## Print parameters for this run
            print(f"Experiment num. {experiment}, replication {replication}. \n "
            f"iat = {input_data_dict['iat'][experiment]}, server_time = {input_data_dict['server_time'][experiment]}, "
                  f"seed = {lst_seeds[replication]}")

            df_settings = df_settings.append({'experiment':experiment, 'replication':replication}, ignore_index=True)
            df_settings['iat'] = input_data_dict['iat'][experiment]
            df_settings['server_time'] = input_data_dict['server_time'][experiment]

            ## Run and reset AltWalker
            walker.run()
            previous_data = planner.get_data() # Get graph variables at end of run
            previous_data_filter = {k: v for k, v in previous_data.items() if k in df_outputs.columns}
                # Filter to relevant outputs
            df_outputs = df_outputs.append(previous_data_filter, ignore_index=True) # Append results f this run
            gw_service.kill() # End associated Java process

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

## Analysis of multiple runs
df_settings['rho_analytical'] = df_settings['server_time'] / df_settings['iat']
df_results = pd.concat([df_settings, df_outputs], axis=1)
print(df_results)

# Get percentage of runs that have good occupancy values according to test script
occupancy_value_counts = df_results['occupancy_verdict'].value_counts(normalize=True)
if 'passed' in occupancy_value_counts:
    occupancy_perc_passed = occupancy_value_counts['passed'] * 100
else:
    occupancy_perc_passed = 0

# Get mean of means for occupancy per experiment
df_results['occupancy_mean'] = pd.to_numeric(df_results['occupancy_mean'], errors='coerce')
rho_series = df_results.groupby('experiment')['rho_analytical'].first()
occupancy_means = df_results.groupby('experiment')['occupancy_mean'].mean()
occupancy_means_series = pd.concat([rho_series, occupancy_means], axis=1)

# Check if values have variance
occupancy_has_no_variance = df_results['occupancy_mean'].var() == 0
if occupancy_has_no_variance:
    raise Exception(
        "No variance in mean occupancy values over time across different runs. Seed is probably not implemented well in SUT.")

# Get fraction of runs that have good delta values according to test script
delta_relative_value_counts = df_results['delta_relative_verdict'].value_counts(normalize=True)
if 'passed' in delta_relative_value_counts:
    delta_relative_perc_passed = delta_relative_value_counts['passed'] * 100
else:
    delta_relative_perc_passed = 0

## Make verdicts
verdict = 'PASSED'

# Percentage of runs where occupancy was within accepted range of analytical solution
if occupancy_perc_passed >= min_perc_within_bandwidth_occupancy: # 40% of runs should be within accepted range
    msg = f"Experiments PASSED: {occupancy_perc_passed} % of runs has occupancy value within bandwidth. Required was {min_perc_within_bandwidth_occupancy}"
else:
    msg = f"Experiments FAILED: {occupancy_perc_passed} % of runs has occupancy value within bandwidth. Required was {min_perc_within_bandwidth_occupancy}"
    verdict = 'FAILED'
print(msg)

# Means of means of occupancy per experiment
print("Means of means of occupancy, compared to analytical value:")
print(occupancy_means_series)

# Percentage of runs where deviation from Little's law (|W - L / lambda) / W) < 1 %
if delta_relative_perc_passed < min_perc_within_bandwidth_delta_relative:
    msg = f"Experiment FAILED: Not {min_perc_within_bandwidth_delta_relative} % of relative delta values are within accepted range, only {delta_relative_perc_passed} %. Required was {min_perc_within_bandwidth_delta_relative} %."
    verdict = 'FAILED'
else:
    msg = f"Experiment PASSED. {delta_relative_perc_passed} % of delta values are within accepted range."

print(msg)
print(f"Overall verdict of analysis of results: {verdict}")

df_results.to_csv('results.csv')

## Get execution time
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Execution time: {elapsed_time:.2f}")
