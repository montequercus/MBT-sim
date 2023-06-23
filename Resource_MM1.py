import salabim as sim


class Source(sim.Component):
    def process(self):
        while True:
            # Create a client
            Client
            # Wait for interarrival time, until next Client is created. Exponential distribution for a Poisson process
            yield self.hold(sim.Exponential(iat).sample())

class Client(sim.Component):
    def process(self):
        # Request position in server, enter its 'requesters' queue
        yield self.request(server)
        # Leave server
        yield self.release(server)
        # Terminate client
        yield self.passivate()

class Server(sim.Resource):
    def process(self):
        # Hold client in service for time taken from exponential distribution
        yield self.hold(sim.Exponential(server_time).sample())
        # Activate client; it will terminate
        self.client.activate()

env = sim.Environment(trace=True)
iat = 10
server_time = 5

Source()
server = Server(capacity=1)

env.run(till=5000)

server.print_statistics()


server.requesters().length.print_histogram()
server.requesters().length_of_stay.print_histogram()