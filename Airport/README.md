# Description
This SUT is a simple ABM of two servers with queue and capacity 1. The servers are placed in series. Passengers are randomly generated, and traverse through the system. The passengers have some walking time between the servers.
This is a simplified version of a model called _Airport_.

The test package can test two similar components within this SUT: 'Passport check' and 'Luggage placing'. These are servers with queue. The test model will monitor arrivals and departures from a server in the SUT. It will test whether the service times are within the expected distributions.

# How to run
This test package can be executed in two ways. Note that the SUT is placed in the 'tests' folder; this is so that it can also be run from the CLI. 

## 1. From CLI
To execute from the CLI, use from this folder:
```console
altwalker online -m models/Components.json "weighted_random(requirement_coverage(100))" tests
```

This will run the test, and use predefined settings for the SUT as given in `test.py`.

## 2. From test execution script
A single test run can be started by executing `Airport_test_execution.py`.

The test model only tests one component, a server with queue, from the SUT. Which component is tested, can ] be selected from the test script by setting `server_under_test`. This can be changed to either `passport_check` or `luggage_placing`. The following (expected) properties of these servers are then passed to the abstract model as graph variables:
- `service_time_min`: Minimal service time at server
- `service_time_max`: Maximal service time at server
- `server name`: Name of server

The following settings of the SUT can be set from the test execution script:
- `seed_SUT`: The seed used by Mesa in the SUT.

The following settings for the test run can be set from the test execution script:
- `t_end`: The number of ticks in the SUT, at which the test should end.
- `show_messages`: Boolean. If True, the messages sent by the SUT will be printed.

# Faulty SUT
The SUT tested here is `Two_server_ABM_better.py`. A very similar model `Two_server_ABM.py` is provided as well. This SUT has some faults: the number in queue is sometimes not updated correctly, because all agents are executed in a random order. This SUT can be tested by changing line 5 in `test.py` to:
```
from . import Two_server_ABM as SUT
```

Running a test with this SUT can demonstrate how the test package detects failures of the SUT.



