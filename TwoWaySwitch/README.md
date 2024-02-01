# Description
## System under test
The system under test (SUT) is a simple agent-based model (ABM) written using `mesa`. It models the behavior of a light that is controlled by 2 or more switches. The switches toggle their positions from 0 to 1 at random intervals taken from a uniform distribution. When the position of a switch changes, it toggles the power state of the light, which is either on or off. This results in Exclusive-OR logic, where the positions of the switches are the inputs, and the power state of the light is the output.

## Test package
The test package tests one simulation run of the SUT, until a simulation end time `max_ticks` is reached.

It tests whether exclusive-OR logic still holds, when one of the switches is toggled.


# How to execute
The test package can be run by executing the test execution script `TwoWay_test_execution.py`, in a Python environment that has `altwalker`. 
Running tests from the CLI will not work here, because of the folder structure, where the SUT is not in the `tests` folder.

The following variables of the SUT can be set from the test execution script:
- `seed`: The seed used by Mesa in the SUT.
- `num_switches`: The number of switches that are modeled in the SUT.
- `min_interval`: The minimum interval, before a switch will toggle its position.
- `max_interval`: The maximum interval, before a switch will toggle its position.

The following graph variables of the abstract model can be set from the test execution script:
- `max_ticks`: Number of ticks of SUT, where test will end.

The test is run with stop condition `"random(vertex_coverage(100))"`. This ensures that when the last vertex `v_data_collected` is reached in the abstract model, the test execution will stop. This vertex can only be reached if `ticks >= max_ticks`. 


