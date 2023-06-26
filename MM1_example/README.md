This is example applies model-based testing (MBT) to a simulation model of a M/M/1 queue. 
The system under test (SUT) is a discrete-event simulation model made using salabim. It is taken from the [MMc example](https://github.com/salabim/salabim/blob/master/sample%20models/MMc.py) of salabim.


# Instructions
The test script can be run in the CLI as follows:
```
altwalker online -m models/MM1_FIFO.json "random(length(500))" tests
```

### Explanation of generator option
The generator option `random(length(500))` will result in a randomly generated test path of 500 elements (vertices or edges). Of course, this number can be changed. A higher number of elements will simply give more times that the SUT's simulation time is advanced, in this case.

Some public AltWalker examples use generator options like `random(vertex_coverage(100))` and `random(edge_coverage(100))`. Those would make paths were 100% of the vertices or edges in the model are covered. However, in this example, 100% coverage cannot be guaranteed. Guards prevent the 

# Progress
The test script currently checks the dynamic behaviour of the simulation model. 

The steady-state behaviour is tested after the simulation run finishes, in the function `tearDownModel()`. Statistics are calculated for the results, and a student t test is done with the analytical solution. This test will likely fail (the main is not within the confidence interval), because:
1. The simulation time may be too low to reach a steady-state solution.
2. Even for high simulation time, the Salabim model will output a slightly lower mean than the analytical solution.

*To do:* Change to SUT to versions of the simulation model that have some fault built in. See how the test can be used to detect these faults.

# Description
## Abstract model
The abstract model looks like this in GraphWalker Studio:
![[MM1_abstract_model.png]]

### Variables (graph data)
The abstract model has two variables (graph data):
1. `t`: simulation time
2. `q`: number of clients in queue
In this example, the abstract model and test script are set up such that the graph data is only updated through the test script, based on the SUT output. Thus, the variables `t` and `q` are only declared (with JavaScript) in the abstract model file.
The graph data is used for guards on all edges.

The definition of `queue` is important to note. In the SUT, the queue is specifically the Queue instance `servers.requesters()`. This is the queue that clients will enter, when there is already a client in `servers.claimers()` (which confusingly is also a Queue instance). 

### Concept
The abstract model is largely based on the state of the queue. The three most important states are:
1. None are in queue.
2. One is in queue.
3. Multiple are in queue.
The edges between these states have guards of the variable `q`, the number of people in queue.

With this set-up, the random path generation of AltWalker actually has little options to be random. This is because there are significant guards on all edges

## Test script
*To be written.*

### Time advancement
The simulation time of the SUT is advanced by using its `step()` function. This advances time to the next scheduled event, and thereby executes the event.

In this example, the `step()` function is often placed at the end of a vertex's method. It may seem more intuitive to place time advancement on an edge, as it is a state transition. That is where one would place it in a FSM.
However, the problem is that the edges also contain the guards. The next vertex that the abstract model can go to is determined by these guards. Thus, if time advancement would be placed on edges, it would be executed *after* evaluating the guards. While logically, the next event should be executed before the guards are evaluated.


## System under test
*To be written*

