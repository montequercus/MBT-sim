import salabim as sim
import random
import time

## Salabim simulation model
class ClientGenerator(sim.Component):
    def process(self):
        while True:
            Client()
            yield self.hold(inter_arrival_time_dis.sample())

class Client(sim.Component):
    def process(self):
        yield self.request(clerks)
        yield self.hold(service_duration_dis.sample())
        yield self.release(clerks)

env = sim.Environment(trace=False)
number_of_clerks = 1
iat = 1
server_time = 0.9
inter_arrival_time_dis = sim.Exponential(iat)
service_duration_dis = sim.Exponential(server_time)
clerks = sim.Resource(name="clerks", capacity=number_of_clerks)

## Rename Salabim's statistics outputs for later comparison to analytical solutions
def make_outputs(clerks):
    # Mean values
    L_q = clerks.requesters().length.mean()
    L_s = clerks.claimers().length.mean()
    L = L_q + L_s # Assumption

    W_q = clerks.requesters().length_of_stay.mean()
    W_s = clerks.claimers().length_of_stay.mean()
    W = W_q + W_s # Assumption

    occupancy = clerks.occupancy.mean()
    occupancy_data = clerks.occupancy.tx()[1] # Data over time

    return L, L_q, W, W_q, occupancy, occupancy_data



## Do a simulation run with fixed settings directly from this script
if __name__ == "__main__":
    # Run model
    ClientGenerator()

    end_sim_time = 10000
    random.seed(time.time())
    env.random_seed(random.randint(1,123456))
    env.run(till=end_sim_time)

    # Create outputs
    L, L_q, W, W_q, occupancy, occupancy_data = make_outputs(clerks)
    print(f'Occupancy: {occupancy}')
