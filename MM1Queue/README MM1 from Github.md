This example applies model-based testing (MBT) to a simulation model of a M/M/1 queue. 
The system under test (SUT) is a discrete-event simulation model made using salabim. It is taken from the [MMc example](https://github.com/salabim/salabim/blob/master/sample%20models/MMc.py) of salabim.


# How to run

## Options for test execution
There are three options to run the test package

## 1. One run from CLI
The test package can be run in the CLI, in a Python environment that has `altwalker`, from this folder as follows:
```
altwalker online -m models/MM1_FIFO_with_s_and_fail.json "weighted_random(requirement_coverage(100) or length(100000))" tests
```

This will do one test run at the standard settings defined in the test script `test.py` and SUT.

## 2. One run from a test execution script
The test execution script `MM1_test_execution_one_run.py` can be executed in a Python environment that has `altwalker`. This will run a test for one simulation run of the SUT.

The following variables of the SUT can be set from the test execution script. Note that these are passed to the SUT via graph variables:
- `iat`: inter-arrival time in seconds
- `server_time`: server time in seconds
- `seed`: seed used in SUT by Salabim

The following graph variables (of the abstract model) can be set from the test execution script, to influence the test run:
- `t_end`: Simulation end time. When the SUT reaches this logical time, the test should end. Note: the simulation will not end at exactly this logical time, but at the first event that comes after it.

The following AltWalker settings can be set from the test execution script:
- `bool_print_paths`: Boolean to print test paths with `ClickReporter()` if True, or to execute without printing paths if False.

## 3. Multiple runs with sampled input parameters from a test execution script
The test execution script `MM1_test_execution_batch_run.py` can be executed in a Python environment that has `altwalker`. This will tests multiple simulation runs of the SUT. A new GraphWalker service and client, and new AltWalker API objects, are made for each new simulation run that is tested. 

The input parameter `server_time` is now sampled from a range. The `seed` used by the SUT is now randomly generated.

The experimental setup can be changed from the test execution script using:
- `num_experiments`: The number of sets of input parameters for which the SUT is tested.
- `num_replications`: The number of replications, meaning the number of times that one set of input parameters is tested again on the SUT, using different seeds each time.

### Verification of results
The goal of running tests with different input parameters is to verify that the SUT's results are correct, given the analytical solutions that are known for a M/M/1 queue. The test model will therefore give a verdict at the end of each test case, on whether the time-average (steady-state) values for $\rho$ and $\delta / W$ are as expected. Furthermore, the test execution script can therefore collect the end results of multiple SUT runs, and do further analysis.

The following settings can be changed for the analysis of results:
- `accepted deviation occupancy`: The accepted deviation from the analytical solution for the occupancy $\rho$. Thus: $(|\rho_{analytical} - \rho| / \rho_{analytical}) * 100%$.
- `accepted_deviation_delta_relative`: The accepted deviation of Little's law, defined as $\delta = |W - L / \lambda|$, as a percentage of the results for $W$. Thus: $(|W - L / \lambda| / W) * 100%$.
- `min_perc_within_bandwidth_occupancy`: The minimum percentage of runs that should have a time-average $\rho$ that is within the accepted range.
- `min_perc_witinh_bandwidth_delta_relative`: The minimum percentage of runs that should have a time-average $\delta / W$ that is within the accepted range.

Note that the variance in results is highly dependent on the simulation end time. The variance only becomes steady after $t = 100000$ s (approximately). However, running a test until this logical time would result in very high execution times and possibly errors regarding TCP/IP (see below). 

# Problem with TCP/IP
A problem is encountered regarding communication between AltWalker and GraphWalker. This communication is done via TCP/IP. However, a new port is opened for every request. As this test package tests every event that the SUT produces, and the SUT produces many events quickly, this will eventually result in an error: your computer system will run out of TCP/IP ports. To prevent this, the test script `test.py` will pause execution after it has done 1000 time advancements of the SUT. The execution of Python is paused for 121 minutes, because all TCP/IP ports will be closed after 2 minutes on Windows.
This value of 1000 is found by trial-and-error, with some safety margin.




