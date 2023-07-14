import salabim as sim
import random

## Adapted from M/M/c example, found on: https://github.com/salabim/salabim/blob/master/sample%20models/MMc%20animated.py
## This file will build and run the simulation model. Unlike 'MM1' which won't run the model.

## Simulation run settings
end_sim_time = 600 # Simulated time at which simulation will stop
bool_print_statistics = True # Toggle print of statistics outputs

iat = 10 # Inter-arrival time
server_time = 5 # Server time

random.seed()
seed = random.randint(0,1234567) # Make random seed for Salabim

## Simulation model
class Client(sim.Component):
    def process(self):
        # Salabim instructions
        self.enter(system)
        yield self.request(servers)
        yield self.hold(sim.Exponential(server_time, 'seconds').sample())
        self.leave()

class ClientGenerator(sim.Component):
    def process(self):
        while True:
            Client()
            yield self.hold(sim.Exponential(iat, 'seconds').sample())

## Initialize model
env = sim.Environment(trace=False, time_unit='seconds', random_seed=seed)
system = sim.Queue("system")
servers = sim.Resource(name="servers", capacity=1)
ClientGenerator()

## Statistics functions
def make_outputs(system,servers):
    L = system.length.mean() # Number in system
    L_q = servers.requesters().length.mean() # Number in queue
    L_s = servers.claimers().length.mean() # Number in service

    W = system.length_of_stay.mean() # Time in system
    W_q = servers.requesters().length_of_stay.mean() # Time in queue
    W_s = servers.claimers().length_of_stay.mean() # Time in service

    return L, L_q, W, W_q

## Run simulation
env.run(till=end_sim_time)
L, L_q, W, W_q = make_outputs(system,servers)

## Print statistics outputs
if bool_print_statistics:
    system.print_statistics()
    servers.print_statistics()
    print(f"L. Number in system: {L} \n L_q. Number in queue: {L_q} \n W. Time in system: {W} \n W_q. Time in queue {W_q}")