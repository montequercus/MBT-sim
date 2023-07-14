from functools import reduce
from operator import xor
import unittest
import sys
# Add parent folder to path. EDIT PATH!
sys.path.append('C:/Users/Ferd/Desktop/Thesis/MBT-sim/ABM_example')

## Import SUT
from TwoWaySwitch import Room, Switch, Light

## Useful functions
def count_class_instances(agent_list, class_name):
    """
    Count the number of instance of an agent (class) in an agent list.
    :param agent_list: (list)
    :param class_name: (class)
    :return: (int) num_of_class
    """
    num_of_class = sum(1 for agent in agent_list if isinstance(agent, class_name))
    return num_of_class


## Test cases
class TwoWay_process(unittest.TestCase):
    def setUpModel(self, data):
        # Initialize Mesa model
        self.num_switches = 2 # Number of switches for one light
        self.num_ticks = 50 # Number of ticks until test script will stop advancing the simulation's time
        data["max_ticks"] = self.num_ticks
        self.model = Room(num_switches=self.num_switches)

    def v_existence(self):
        # Start vertex. Assert that the specified number of agents is initialized.
        num_switches_ver = count_class_instances(self.model.schedule.agents, Switch)
        num_lights_ver = count_class_instances(self.model.schedule.agents, Light)
        self.assertEqual(num_switches_ver, self.num_switches)
        self.assertEqual(num_lights_ver, 1)

    def e_initialize(self):
        # Save instances of Switch agents as a list in this test
        self.switch_agents = [agent for agent in self.model.schedule.agents if isinstance(agent, Switch)]

        # Make dictionaries with memories of counter and position values
        counter_values_init = [[agent.counter] for agent in self.switch_agents]
        self.dict_counter_memory = dict(zip(self.switch_agents, counter_values_init))
        print(self.dict_counter_memory)

        position_values_init = [[agent.position] * 2 for agent in self.switch_agents] # Repeat to initialize memory of size 2
        self.dict_position_memory = dict(zip(self.switch_agents, position_values_init))
        print(self.dict_position_memory)

    def v_ticks(self, data):
        # Assert that the number of ticks is equal between the SUT and the abstract model
        self.assertEqual(self.model.schedule.steps, int(data["ticks"]), msg="Current tick of SUT model is different from current tick according to abstract model.")

    def e_step(self):
        # Model action: ticks++
        # Advance time with step function in Mesa.
        self.model.step()

    def v_counters(self, data):
        # Verify that counter of switch agents are within their domain
        for agent in self.switch_agents:
            self.assertGreaterEqual(agent.counter, 0, msg=f"Agent {agent}: Counter below 0.")
            self.assertLessEqual(agent.counter, self.model.max_interval, msg=f"Agent {agent}: Counter higher than maximum interval.")

        # Update test's memory of counters
        for k,_ in self.dict_counter_memory.items():
            # Add 'counter' of agent to list in dictionary, slice so last two items are kept.
            list_last_two = self.dict_counter_memory[k][-1:]
            list_last_two.append(k.counter)

            self.dict_counter_memory[k] = list_last_two
            print(self.dict_counter_memory)

        # Verify that counters have decreased by 1
        for k,v in self.dict_counter_memory.items():
            # Only do check when counter has not been reset in previous step
            if v[-2] > 0:
                difference = v[-2] - v[-1]
                self.assertTrue(difference,1)

        # Check whether a counter is 0, for the guards
        for agent in self.switch_agents:
            if agent.counter == 0:
                # Pass to abstract model that a counter is 0
                data['bool_counter_zero'] = True


    def e_counting(self):
        # Guard: bool_counter_zero = false
        pass

    def e_counter_empty(self, data):
        # Guard: bool_counter_zero = true
        data['bool_counter_zero'] = False # Reset boolean for next tick

    def v_position(self):
        # Verify that position has changed when counter has reached 0
        # !! To be implemented.
        pass

    def e_switch(self):
        # Move to 'v_power'
        pass

    def v_power(self):
        debug = True
        if debug:
            # Intermediate output from DataCollector
            int_output = self.model.datacollector.get_model_vars_dataframe()
            print(int_output)

        # Test XOR logic of inputs (switch positions) vs output (light power state)
        switch_positions = [agent.position for agent in self.switch_agents] # List of agent positions
        power_ver = reduce(xor, map(bool, switch_positions)) # Check XOR for list

        # Assert that current light power state follows XOR logic
        self.assertEqual(self.model.light.power, power_ver)

    def e_complete(self):
        # Move to 'v_ticks'
        pass

    def e_stopped(self):
        # Guard: ticks == max_ticks
        # Stop time advancement, move to 'v_data_collected'
        self.output = self.model.datacollector.get_model_vars_dataframe()

    def v_data_collected(self):
        # Check if process is stopped after specified number of ticks
        self.assertEqual(self.model.schedule.steps, self.num_ticks)

        # Check size of datacollector output compared to model settings
        self.assertEqual(self.output.shape[0], self.num_ticks)

        # Check if 'positions' column of output has the intended data type: all items are a list
        self.assertTrue(self.output['positions'].apply(type).eq(list).all())
        # Check if all items in lists in 'positions' column are Boolean
        self.assertTrue(self.output['positions'].apply(lambda x:
                                                       all(isinstance(i, bool) for i in x)).all())

        # Check if 'power' column has the intended data type: all items are Booleans
        self.assertTrue(self.output['power'].apply(type).eq(bool).all())