import salabim as sim

class CustomerGenerator(sim.Component):
    # Create customers, with an interarrival time of uniform(5,15)
    def process(self):
        while True:
            Customer()
            # Statistical sampling: wait for time until next customer is created
            yield self.hold(sim.Uniform(5, 15).sample())

class Customer(sim.Component):
    def process(self):
        # Place itself at tail of waiting line
        self.enter(waitingline)
        # Check if clerk is idle
        if clerk.ispassive():
            clerk.activate() # Make active if idle

        for clerk in clerks:
            if clerk.ispassive()
                clerk.activate()
                break  # Reactivate only one clerk

        yield self.passivate()

class Clerk(sim.Component):
    def process(self):
        while True:
            # FIFO queue
            while len(waitingline)==0:
                yield self.passivate()
            # Once active, get first customer at of waiting line
            self.customer = waitingline.pop()
            # Hold (this customer) for 30 seconds
            yield self.hold(30)
            # Activate customer; it will terminate
            self.customer.activate()

env = sim.Environment(trace=True)

CustomerGenerator()

## Multiple clerks possible
# clerk = Clerk()
num_clerks = 1
clerks = [Clerk() for _ in range(num_clerks)]


waitingline = sim.Queue("waitingline")

env.run(till=50)
print()
waitingline.print_statistics()