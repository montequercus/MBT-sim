import salabim as sim
import random
import json # For importing parameter values

## Adapted from M/M/c example, found on: https://github.com/salabim/salabim/blob/master/sample%20models/MMc%20animated.py
## This script only initiates a simulation model - it does not run the simulation.

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

## Import parameter values
bool_use_settings_file = False # True: Use settings file. False: Use predefined settings

if bool_use_settings_file:
    # Use a settings file
    with open('SUT_settings.json', 'r') as f:
        params = json.load(f)

    print(f"(Replication according to SUT: {params['rep_num']}")
    seed = params['seed']
    # seed = 10
    iat = params['iat']  # Inter-arrival time (mean)
    server_time = params['server_time']  # Time in server (mean)
else:
    # Use predefined settings and a random seed
    iat = 10
    server_time = 5
    seed = 1
    random.seed()
    seed = random.randint(0,1234567)

## Initialize model
env = sim.Environment(trace=False, time_unit='seconds', random_seed=seed)
system = sim.Queue("system")
servers = sim.Resource(name="servers", capacity=1)
ClientGenerator()


## Statistics functions
def make_outputs(system,servers):
    L = system.length.mean()
    L_q = servers.requesters().length.mean()
    L_s = servers.claimers().length.mean()
    L_server = L_q + L_s

    W = system.length_of_stay.mean()
    W_q = servers.requesters().length_of_stay.mean()
    W_s = servers.claimers().length_of_stay.mean()
    W_server = W_q + W_s

    # system.print_statistics()
    # servers.print_statistics()
    #
    # print(f"L: Time-average number of entities in system: {L:.3f}")
    # print(f"L_q: Time-average number of entities in queue: {L_q:.3f}")
    # print(f"L_s: Time-average number of entities in service: {L_s:.3f}")
    # print(f"L_q + L_s : {L_server:.3f}")
    #
    # print(f"W: Average time in system: {W:.3f}")
    # print(f"W_q: Average time in queue: {W_q:.3f}")
    # print(f"W_s: Average time in service: {W_s:.3f}")
    # print(f"W_q + W_s : {W_server:.3f}")

    return L, L_q, W, W_q

# if bool_use_settings_file:
#     print(params)
# else:
#     env.run(till=650)
#     make_outputs(system, servers)
#     print(f"\n Seed: {seed}")
