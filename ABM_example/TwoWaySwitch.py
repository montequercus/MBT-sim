from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

"""
Simulation model. Implemented as an agent-based model (ABM) using Mesa.
Model: A light is controlled by two switches. The switches will switch at random times, with interval between 'min_interval' and 'max_interval' ticks. A switch event will cause the light to switch on or off
Expected behaviour: The input and output should follow exclusive-OR (XOR) logic during all ticks. The inputs of this XOR gate are the positions of the two switches, and the output is the power state of the light.
"""

## Functions for data collection
def get_positions(model):
    """Return list with positions of switch agents"""
    return [agent.position for agent in model.schedule.agents if isinstance(agent, Switch)]

def get_powerstate(model):
    """Return power state of model"""
    return model.light.power # !CHECK

## Agent definitions
class Switch(Agent):
    def __init__(self, unique_id, model):
        """
        Properties:
        position: bool. Position of light switch
        counter: bool. Number of ticks until next switch event.
        """
        super().__init__(unique_id, model)
        self.position = False
        self.counter = self.random.randint(self.model.min_interval, self.model.max_interval)

    def step(self):
        if self.counter > 0:
            self.counter -= 1 # Count down until 0
        else:
            self.position = not self.position # Set switch to other position
            # Change state of the light, when switch is flipped
            self.model.light.power = not self.model.light.power
            # Reset counter
            self.counter = self.random.randint(self.model.min_interval, self.model.max_interval)

class Light(Agent):
    def __init__(self, unique_id, model):
        """
        Properties:
        power: bool. Power state of light
        """
        super().__init__(unique_id, model)
        self.power = False  # Light is initially off

    def step(self):
        pass  # Light does nothing - it is controlled by the two switches

## Model definition
class Room(Model):
    def __init__(self, light=False, num_switches=2, min_interval=2, max_interval=10, seed=None):
        """
        Properties:
        num_switches: int. Number of switches for the light
        min_interval: int. Minimum length of interval between switch events of one switch
        max_interval: int. Maximum length of interval between switch events of one switch
        """
        super().__init__(seed)
        self.schedule = RandomActivation(self)
        self.num_switches = num_switches
        self.min_interval = min_interval
        self.max_interval = max_interval

        # Make one Light agent and add to scheduler
        self.light = Light(0, self) # Save agent as model property
        self.schedule.add(self.light)

        # Make specified number of switch agents, and add to scheduler
        for i in range(num_switches):
            switch = Switch(i+1, self)
            self.schedule.add(switch)

        # Collect all data, also agent-related data, from within model class
        model_metrics = {
            "positions": get_positions,
            "power": get_powerstate,
        }
        self.datacollector = DataCollector(model_reporters=model_metrics)

    def step(self):
        # Model does nothing, all logic is in agents
        self.schedule.step() # Let all agents perform their step function
        self.datacollector.collect(self) # Collect data

## Run model
debug = True
bool_run_from_script = False # Boolean. True: Run from this file. False: Run from another script
num_switches = 2 # Number of switches for light
num_ticks = 50 # Number of ticks to simulat
seed = 3 # Set a fixed seed for Mesa

if bool_run_from_script:
    model = Room(seed=seed, num_switches=num_switches)
    for i in range(num_ticks):
        model.step()

    ## Get data and export to csv
    model_data = model.datacollector.get_model_vars_dataframe()
    if debug:
        print(model_data)
    model_data.to_csv('mesa_output.csv')