import unittest
import warnings
import logging

# from . import Two_server_ABM_better as SUT # Import SUT from current folder, the 'tests' folder
from . import Airport as SUT
model1 = SUT.Airport(seed=1, logger_level=logging.WARN, show_messages=True)
# Change logger_level to logging.INFO for more info from SUT

def setUpRun():
    pass

def tearDownRun():
    pass

def name_in_list(name, list):
    """
    Check if string is in one of strings in list
    :param name: string
    :param list: list
    :return: bool
    """
    bool_name_in_list = False
    for item in list:
        if name in item:
            bool_name_in_list = True
            break
    return bool_name_in_list

def time_advance(self, data):
    ## First advance time once
    model1.step() # Advance time
    self.time += 1
    # print(f"t = {self.time}, d= {int(data['d'])}")  # debug
    i = 0 # Keep count of consecutive time advancement
    if isinstance(self.time_since_new_service, int):
        self.time_since_new_service += 1 # # Update clock
        #print(self.time_since_new_service)  # Debug

    ## Check for messages for component
    while not name_in_list(self.component_name, model1.messages):
        model1.step() # If no messages, keep advancing time
        i = i+1
        self.time += 1
        # print(f"t = {self.time}, d= {int(data['d'])}") # debug
        if isinstance(self.time_since_new_service, int):
            self.time_since_new_service += 1  # # Update clock
            # print(f"t = {self.time}, time since new service:{self.time_since_new_service}") # Debug
        # warnings.warn(f'{self.time}: NO MESSAGE, TIME ADVANCED')
        if i > 1500: # Prevent infinite while-loop
            warnings.warn('No messages to server for too long.')
            break
    else: # If there is a message, process it
        ## Get number of arrivals and departures from SUT
        S1_arrivals = 0 # Initialize
        S1_departures = 0 # Initialize
        for item in model1.messages:
            if self.component_name in item:
                if 'arrival' in item:
                    warnings.warn(f'{self.time}: ARRIVAL {self.component_name}')
                    S1_arrivals += 1
                    self.total_arrivals += 1
                    self.timestamps_arrivals.append(model1.schedule.time)

                if 'departure' in item:
                    warnings.warn(f'{self.time}: DEPARTURE {self.component_name}')
                    S1_departures +=1
                    self.total_departures += 1

        ## Update graph data for guards
        data['a'] = S1_arrivals
        data['d'] = S1_departures
        data['t'] = self.time
        # print(f"t = {self.time}, d= {int(data['d'])}")  # debug

        ## Update test script data
        num_in_component = self.mem_num_in_component[-1] + S1_arrivals - S1_departures
        self.mem_num_in_component.append(num_in_component)
        self.mem_num_in_component = self.mem_num_in_component[-2:]
        self.num_in_queue = max(0, self.total_arrivals - self.total_departures - 1)

def standard_asserts(self, component, data):
    """
    Asserts to do at every vertex
    """
    ## Check SUT data with graph data. Have guards worked correctly?

    ## Check SUT data with graph data. Have guards worked correctly?
    self.assertEqual(component.num_in_queue, int(data['q']),
                     msg='Number in queue: different in SUT compared to abstract model.')
    self.assertEqual(component.num_in_service, int(data['s']),
                     msg='Number in service: different in SUT compared to abstract model')

    ## Test abstract model to test script
    self.assertEqual(self.num_in_queue, component.num_in_queue,
                     msg="Number in queue: different in test script compared to abstract model.")

    ## Change in number of entities in component may only be 2
    delta_num_in_components = self.mem_num_in_component[-1] - self.mem_num_in_component[0]
    self.assertLessEqual(abs(delta_num_in_components), 2,
                         msg='Number of components has changed by more than 2 during step.')

def print_values(self):
    """
    Make a string of relevant values for warnings and exceptions
    """
    string0 = f'Time: {self.time};'
    string1 = f'Number in component: {self.mem_num_in_component[-1]};'
    string2 = f'Number in queue: {self.num_in_queue};'
    string3 = f'Total departures: {self.total_departures};'
    string4 = f'Total arrivals: {self.total_arrivals};'
    print_string = '\n'.join(string0, string1, string2, string3, string4)
    return print_string

def assert_service_time_within_distribution(self):
    if isinstance(self.time_since_new_service, int):
        self.assertGreaterEqual(self.time_since_new_service, self.service_time_min,
                                msg="Departure (from service) before minimum service time.")
        self.assertLessEqual(self.time_since_new_service, self.service_time_max,
                             msg="Departure (from service) after maximum service time.")

class Server_with_queue(unittest.TestCase):
    def setUpModel(self, data):
        ## Experimental setup
        # if data['t_end'] > 0:
        #     t_end = data['t_end'] # Get simulation end time from graph
        # else:
        #     t_end = 10000 # Set simulation end time in this test script
        # model1.seed = 77 # Seed used by Mesa in SUT
        # self.service_time_min = 30 # Match value of SUT component here!
        # self.service_time_max = 90 # Match value of SUT component here!

        if int(data['t_end']) == 0:
            ## For tests via CLI: set values here
            t_end = 10000 # Simulation end time
            data['t_end'] = t_end
            self.component = model1.luggage_placing # Component under test
            self.component_name = 'Luggage placing'
            model1.seed = 77 # Seed used by SUT
            # self.service_time_min = 30 # Match value of SUT component here!
            # self.service_time_max = 90 # Match value of SUT component here!
            self.service_time_min = 20  # Match value of SUT component here!
            self.service_time_max = 40  # Match value of SUT component here!
        elif int(data['t_end']) > 0:
            ## For test via test execution script: get values from graph variables
            t_end = int(data['t_end'])
            model1.seed = data['seed']
            model1.show_messages = data['show_messages']
            self.component_name = str(data['component_name'])
            self.service_time_min = int(data['service_time_min'])
            self.service_time_max = int(data['service_time_max'])

            # Look up component object
            components = {
                'Passport check': model1.passport_check,
                'Luggage placing': model1.luggage_placing,
                'Passenger scan': model1.passenger_scan,
                'Manual check': model1.manual_check
            }
            self.component = components[self.component_name]
        else:
            raise Exception('t_end is not specified correctly')

        print(f"T_END: {t_end}")

        ## Initialize test script variables
        self.time = 0
        self.mem_num_in_component = [0, 0]
        self.num_in_queue = 0
        self.timestamps_arrivals = []
        self.total_departures = 0
        self.total_arrivals = 0
        self.time_since_new_service = None

        data['t_end'] = t_end

## Vertices
    def v_impossible(self):
        pass

    def v_q0_s0(self, data):
        """
        A. Empty queue, empty server
        q = 0
        s = 0
        """
        self.time_since_new_service = None  # Nobody in service
        standard_asserts(self, self.component, data)

        time_advance(self, data)


    def v_q0_s1(self, data):
        """
        B. Empty queue, 1 in service
        q = 0
        s = 1
        """
        standard_asserts(self, self.component, data)
        time_advance(self, data)

    def v_q1_s1(self, data):
        """
        C. One in queue, one in service
        q = 1
        s = 1
        """
        standard_asserts(self, self.component, data)
        time_advance(self, data)

        ## FIFO of queue: ??

    def v_qZ_s1(self, data):
        """
        D. Multiple in queue, one in service
        q > 1
        s = 1
        """
        standard_asserts(self, self.component, data)
        time_advance(self, data)

    def v_end(self):
        print(f"End of run. t = {self.time}")

    def e_end(self):
        pass

## Edges where a new entity must enter service
    def e_both(self):
        """
        Self-edge for B, C, D
        Guard: a==1 && b==1
        One must enter service
        """
        assert_service_time_within_distribution(self)
        self.time_since_new_service = 0

    def e_departure_to_q0_s1(self):
        """
        C --> B
        Guard: d==1 && a==0
        One must enter service
        """
        assert_service_time_within_distribution(self)
        self.time_since_new_service = 0

    def e_departure_to_q1_s1(self):
        """
        D --> C
        Guard: d==1 && a==0 && q==1
        One must enter service
        """
        assert_service_time_within_distribution(self)
        self.time_since_new_service = 0

    def e_departure_on_qZ(self):
        """
        D --> D
        Guard: d==1 && a==0 && q>1
        One must enter service
        """
        assert_service_time_within_distribution(self)
        self.time_since_new_service = 0

    def e_arrival_to_q0_s1(self):
        """
        A --> B
        Guard: a==1 && d==0
        Arrival to an empty queue.
        One must enter service.
        """
        assert_service_time_within_distribution(self)
        self.time_since_new_service = 0

## Edges where no tests are needed
    def e_arrival(self):
        """
        B --> C, C --> D
        Guard: a==1 && d==0
        No test needed on edge.
        """
        # self.time_since_new_service = 0
        pass

    def e_arrivals_on_qZ(self):
        """
        D --> self
        Guard: a>0 && d==0
        Actions: q=q+a
        No test needed on edge.
        """
        pass

    def e_departure_to_q0_s0(self):
        """
        B --> A
        Guard: d==1 && a==0
        Nobody enters service
        """
        pass

## Unlikely edges: raise warning
    def e_two_arrivals(self):
        """
        A --> C
        Guard: a==2 && d==0
        No action in graph
        """
        warnings.warn('Two arrivals in one time step. \n'+
                      print_values(self))

    def e_two_arrivals_to_qZ(self):
        """
        B --> D, C --> D
        Guard: a==2 && d==0
        No action in graph
        """
        warnings.warn('Two arrivals in one time step. \n' +
                      print_values(self))

    def e_a2_d1(self):
        """
        B --> C
        Guard: a==2 && d==1
        One must enter service
        """
        warnings.warn('Two arrivals and one departure in one time step \n' +
                      print_values(self))
        # !! Enter service

    def e_a2_d1_to_qZ(self):
        """
        C --> D, D --> self
        Guard: a==2 && d==1
        Action: q++
        One must enter service
        """
        warnings.warn('Two arrivals and one departure in one time step \n' +
                      print_values(self))
        ## !! Enter service

## Impossible edges: raise exception
    def e_departure_impossible(self):
        raise Exception("Impossible state transition: component got 'departure' message, while no entities were supposed to be in queue or server.")

    def e_impossible(self, data):
        raise Exception(f"Impossible state transition: component got {int(data['d'])} departures in one time step.")

## End
    def tearDownModel(self):
        print(f"Tests done for server {self.component_name}. \n"
              f"End time: {model1.schedule.time} \n"
              f"Total service time in this server: {self.component.total_service_time} \n"
              f"Total passengers served by this server: {self.component.total_served}")



