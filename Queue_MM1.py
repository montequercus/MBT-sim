import salabim as sim

## Adapted from the "MMc animated example" found on https://github.com/salabim/salabim/blob/master/sample%20models/MMc%20animated.py

class Source(sim.Component):
    def process(self):
        while True:
            # Create a client
            Client
            # Wait for interarrival time, until next Client is created. Exponential distribution for a Poisson process
            yield self.hold(sim.Exponential(iat).sample())

class Client(sim.Component):
    def process(self):
        # Enter the system
        self.enter(system)
        # Enter server directly, or enter its 'requesters' queue
        yield self.request(server)
        # Stay some time 'in service
        yield self.hold(sim.Exponential(server_time).sample())
        # Leave the queue
        self.leave()

env = sim.Environment(trace=False)

iat = 10
server_time = 5

# Actual queue
system = sim.Queue("system")
# Server where entities are 'in service'
server = sim.Resource(name="servers", capacity=1)

Source()

env.run(till=5000)
system.length.print_histogram()