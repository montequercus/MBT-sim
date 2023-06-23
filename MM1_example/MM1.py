import salabim as sim
from itertools import count

## Adapted from M/M/c example, found on: https://github.com/salabim/salabim/blob/master/sample%20models/MMc%20animated.py

class Client(sim.Component):
    _ids = count(0) # Assign IDs to instances of class, in order to count them
    def process(self):
        # Count instances of class
        self.id = next(self._ids)
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

env = sim.Environment(trace=True, time_unit='seconds')

iat = 10
server_time = 5

system = sim.Queue("system")

servers = sim.Resource(name="servers", capacity=1)

ClientGenerator()

# do_animation()
# env.run(till=50)


## Statistics
def make_outputs(system,servers):
    L = system.length.mean()
    L_q = servers.requesters().length.mean()
    L_s = servers.claimers().length.mean()
    L_server = L_q + L_s

    W = system.length_of_stay.mean()
    W_q = servers.requesters().length_of_stay.mean()
    W_s = servers.claimers().length_of_stay.mean()
    W_server = W_q + W_s

    system.print_statistics()
    servers.print_statistics()

    print(f"L: Time-average number of entities in system: {L:.3f}")
    print(f"L_q: Time-average number of entities in queue: {L_q:.3f}")
    print(f"L_s: Time-average number of entities in service: {L_s:.3f}")
    print(f"L_q + L_s : {L_server:.3f}")

    print(f"W: Average time in system: {W:.3f}")
    print(f"W_q: Average time in queue: {W_q:.3f}")
    print(f"W_s: Average time in service: {W_s:.3f}")
    print(f"W_q + W_s : {W_server:.3f}")





# print(f"Average time in system: {system.length_of_stay.mean()}")
# print(f"Time-average number in system: {system.length.mean()}")


