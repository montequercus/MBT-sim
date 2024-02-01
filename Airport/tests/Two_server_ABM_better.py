import mesa
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from enum import Enum
import scipy.stats as stats
import numpy as np
import logging
import sys

# Set up logging
logger = logging.getLogger('new_logger')
logger.propagate = False
s_handler = logging.StreamHandler(sys.stdout)
s_handler.setLevel(logging.INFO)
logger.addHandler(s_handler)

"""
This model uses two schedulers, so that values for queue lengths are only updated after all passengers have moved.
"""

class ServerWithQueue(mesa.Agent):
    def __init__(self, model, name, distribution):
        super().__init__(self, model)
        self.model = model
        self.name = name
        self.distribution = distribution
        # self.capacity = capacity

        ## Queue lists and variables
        self.queue = []
        self.num_in_queue = 0 # Total number in queue at end of tick
        self.passenger_in_service = None
        self.num_in_service = 0 # Total number in service at end of tick

        ## Statistics
        self.total_queue_time = 0
        self.total_service_time = 0
        self.total_queued = 0
        self.total_served = 0

        # self.total_time_utilized = 0
        self.utilization = 0

    def enter(self, passenger):
        if not self.passenger_in_service:
            self.enter_service(passenger)
        else:
            self.enqueue(passenger)

    def enter_service(self, passenger):
        self.passenger_in_service = passenger
        passenger.service_time_remaining = self.distribution.rvs()
        logger.info(f"t = {self.model.schedule.time}: {self.name}: Passenger {passenger.unique_id} enters service.")

    def enqueue(self, passenger):
        self.total_queued += 1
        self.queue.insert(0, passenger)
        passenger.queue_start_time = self.model.schedule.time
        logger.info(f"t = {self.model.schedule.time}: {self.name}: Passenger {passenger.unique_id} enters queue.")

    def release(self, passenger):
        self.passenger_in_service = None # Reset
        passenger.service_time_remaining = 0 # Reset to avoid confusion
        logger.info(f"t = {self.model.schedule.time}: {self.name}: Passenger {passenger.unique_id} released from service.")
        passenger.go_to_next_action()
        ## Send message that an agent departs from this server.
        self.model.messages.append('departure ' + self.name)

    def dequeue(self):
        first_in_queue = self.queue.pop() # Select and remove from queue
        first_in_queue.queue_end_time = self.model.schedule.time
        time_in_queue = first_in_queue.queue_end_time - first_in_queue.queue_start_time
        self.model.dict_times_in_queue[self.name].append(time_in_queue)

        self.enter_service(first_in_queue)

    def step(self):
        ## Release passengers from service when possible
        if self.passenger_in_service:
            if self.passenger_in_service.service_time_remaining > 1:
                self.passenger_in_service.service_time_remaining -= 1
            else:
                self.release(self.passenger_in_service)
                self.total_served += 1

        self.num_in_queue = len(self.queue) # Update during time step to use here
        ## Fill up new places from queue
        if self.num_in_queue > 0:
            if not self.passenger_in_service:
                self.dequeue()
            else:
                pass
        else:
            # Case: nobody in queue or server
            pass

        ## Output of tick
        self.num_in_service = 1 if bool(self.passenger_in_service) else 0
        self.num_in_queue = len(self.queue)
        # logger.info(f"t = {self.model.schedule.time}, {self.name} has queue: {self.queue}")

        ## Keep statistics
        if self.num_in_service == 1:
            self.total_service_time += 1
        self.utilization = self.total_service_time / self.model.schedule.time if self.model.schedule.time>0 else 0

class PassengerSource(mesa.Agent):
    def __init__(self, unique_id, model, distribution):
        super().__init__(unique_id, model)
        self.distribution = distribution
        self.inter_arrival_time = 0
        self.inter_arrival_time_remaining = 0
        self.id_for_passenger = 0 # Unique ID for newly created passengers

    def step(self):
        if self.inter_arrival_time_remaining > 0:
            self.inter_arrival_time_remaining -= 1
        else:
            self.id_for_passenger += 1
            logger.info(f"t = {self.model.schedule.time}: PassengerSource: Created passenger {self.id_for_passenger}")
            passenger = Passenger(self.id_for_passenger, self.model)
            self.model.schedule.add(passenger)
            self.model.messages.append('departure Passenger source')

            ## Take a new inter-arrival time
            self.inter_arrival_time = self.distribution.rvs()
            self.inter_arrival_time_remaining = self.inter_arrival_time

class PassengerAction(Enum):
    SHOW_PASSPORT = 1
    PLACE_LUGGAGE_ON_BELT = 2
    # ENTER_PASSENGER_SCAN = 3
    # ENTER_MANUAL_PASSENGER_CHECK = 4
    # PICK_UP_LUGGAGE = 5

distances = {
    PassengerAction(1): 5,
    PassengerAction(2): 5,
    # PassengerAction(3): 5,
    # PassengerAction(4): 5,
    # PassengerAction(5): 10
}

def calculate_walking_time(self, distance):
    walking_time = distance / self.walking_speed
    return walking_time

class Passenger(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.walking_speed = stats.uniform(0.611, scale=0.777-0.611).rvs()
        # self.bool_needs_manual_check = stats.uniform(0,1).rvs() <= self.model.probability_manual_check

        self.actions = iter(PassengerAction)
        self.go_to_next_action()

        self.service_time = 0
        self.service_time_remaining = 0

        # self.bool_luggage_on_belt = False
        # self.bool_luggage_at_end = False
        # self.time_luggage_at_end = 0
        # self.time_waiting_for_luggage = 0
        # self.luggage_time_remaining = 0

        self.time_of_creation = self.model.schedule.time
        self.time_of_termination = None

    def go_to_next_action(self):
        self.service_time_remaining = 0 # Reset to avoid confusion
        self.current_action = next(self.actions, 'terminate')
        logger.info(msg=f't = {self.model.schedule.time}: Passenger {self.unique_id}: current action: {self.current_action}')
        if self.current_action == 'terminate':
            self.terminate()
        else:
            self.associated_server = self.model.dict_servers[self.current_action]
            self.bool_is_walking = True
            self.walking_time_remaining = calculate_walking_time(self, distances[self.current_action])

    def terminate(self):
        self.time_of_termination = self.model.schedule.time
        throughput_time = self.time_of_termination - self.time_of_creation
        self.model.lst_throughput_times.append(throughput_time) # Keep record
        logger.info(msg=f't = {self.model.schedule.time}:   Passenger {self.unique_id}: leaves system. Throughput time: {throughput_time}')
        self.model.schedule.remove(self)

    def step(self):
        ## Check if passenger is walking or in service
        if self.bool_is_walking:
            if self.walking_time_remaining > 0:
                self.walking_time_remaining -= 1
            else:
                logger.info(f"t = {self.model.schedule.time}: Passenger {self.unique_id} is done walking, enters {self.associated_server.name}")
                self.walking_time_remaining = 0  # Reset to avoid confusion
                self.bool_is_walking = False
                ## Send message that a passenger joins its next server.
                self.model.messages.append('arrival ' + self.associated_server.name)

                ## Use server's functions to enter either queue or server
                self.associated_server.enter(self)

        else:
            pass

distributions = {
    'Arrivals': stats.uniform(loc=50, scale=20), # Arrivals
    PassengerAction(1): stats.triang(c=0.25, loc=30, scale=60), # Passport check
    PassengerAction(2): stats.uniform(loc=20, scale=20), # Luggage dropoff
    # PassengerAction(2): stats.uniform(loc=40, scale=20), # Luggage dropoff WRONG
    # PassengerAction(3): stats.uniform(loc=30, scale=55), # Passenger scan
    # PassengerAction(4): stats.uniform(loc=120, scale=180), # Manual scan
    # PassengerAction(5): stats.uniform(loc=20, scale=20) # Luggage pickup
}

class Airport(mesa.Model):
    def __init__(self, seed=1, distributions=distributions, logger_level=logging.INFO, show_messages=True):
        ## Use same seed for random distributions
        self.random = np.random.default_rng(seed)
        np.random.seed(seed)

        ## Set up logger and messages
        logger.setLevel(logger_level)
        self.show_messages = show_messages

        ## Make servers and add to scheduler
        self.schedule = RandomActivation(self)
        self.schedule2 = RandomActivation(self)

        self.passenger_source = PassengerSource(unique_id=-1, model=self,
                                                distribution=distributions['Arrivals'])
        self.schedule.add(self.passenger_source)

        self.passport_check = ServerWithQueue(self, 'Passport check', distributions[PassengerAction(1)])
        self.luggage_placing = ServerWithQueue(self, 'Luggage placing',
                                               distributions[PassengerAction(2)])
        self.schedule2.add(self.passport_check)
        self.schedule2.add(self.luggage_placing)

        self.dict_servers = {
            PassengerAction.SHOW_PASSPORT: self.passport_check,
            PassengerAction.PLACE_LUGGAGE_ON_BELT: self.luggage_placing,
            # PassengerAction.ENTER_PASSENGER_SCAN: self.passenger_scan,
            # PassengerAction.ENTER_MANUAL_PASSENGER_CHECK: self.manual_check,
            # PassengerAction.PICK_UP_LUGGAGE: self.luggage_pickup
        }

        ## Passenger properties
        self.probability_manual_check = 0.1

        ## Keep records
        self.lst_throughput_times = []
        self.servers_with_queue = [server for server in self.dict_servers.values() if
                                   isinstance(server, ServerWithQueue)]
        self.dict_times_in_queue = {server.name: [] for server in self.servers_with_queue}

        ## Output per tick
        self.num_passengers_in_system = 0
        self.num_passengers_processed = 0
        self.messages = [] # List of events that happened during tick

    def step(self):
        self.messages = [] # Reset list of events
        self.schedule.step() # Let all passengers and PassengerSource do a step
        self.schedule2.step() # Let all servers do a step

        if self.show_messages and self.messages:
            logger.warning(f't = {self.schedule.time}: messages: {self.messages}')

## Run model
model = Airport(seed=1, logger_level=logging.INFO, show_messages=True)

if __name__ == "__main__":
    for i in range(0, 20):
        model.step()

        ## Check for arrival and departure messages for one server
        S1_arrivals = 0
        S1_departures = 0
        for item in model.messages:
            if 'Passport check' in item:
                if 'arrival' in item:
                    S1_arrivals += 1
                if 'departure' in item:
                    S1_departures +=1
        logger.info(f"t = {model.schedule.time}: Model: {S1_arrivals} arrival(s) in Passport check")
        logger.info(f"t = {model.schedule.time}: Model: {S1_departures} departure(s) in Passport check")




























