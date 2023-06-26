from ema_workbench import IntegerParameter, ScalarOutcome, Model, perform_experiments, SequentialEvaluator, ema_logging, analysis
import salabim as sim
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import math

iat=10
server_time=5


## Simulation model as function
def run_MM1_sim(seed_setting, num_steps=100000, iat=iat, server_time=server_time):
    # Settings
    env = sim.Environment(trace=False, time_unit='seconds', random_seed=seed_setting)

    ## Salabim model classes
    class Client(sim.Component):
        # _ids = count(0) # Assign IDs to instances of class, in order to count them
        def process(self):
            # Count instances of class
            # self.id = next(self._ids)
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

    # Set-up
    system = sim.Queue("system")
    servers = sim.Resource(name="servers", capacity=1)
    ClientGenerator()

    # Run
    env.run(till=num_steps)

    # Output
    L_system = system.length.mean()
    L_queue = servers.requesters().length.mean()
    W_system = system.length_of_stay.mean()
    W_queue = servers.requesters().length_of_stay.mean()
    return L_system, L_queue, W_system, W_queue


model = Model("MM1", function=run_MM1_sim)

model.uncertainties = [
    IntegerParameter("seed_setting",0,99999)
]

model.outcomes = [
    ScalarOutcome("L_system"),
    ScalarOutcome("L_queue"),
    ScalarOutcome("W_system"),
    ScalarOutcome("W_queue"),
]


with SequentialEvaluator(model) as evaluator:
    results = evaluator.perform_experiments(scenarios=1000)

experiments, outcomes = results

## Convert outcomes to long-form dataframe
outcomes_df = pd.DataFrame.from_dict(outcomes, orient='columns').reset_index()

means = outcomes_df.mean()
stds = outcomes_df.std()
print(means)
print(stds)

outcomes_df = pd.melt(outcomes_df, id_vars='index', value_vars = list(outcomes.keys()))

## Get analytical solution
lambd = 1 / iat
mu = 1 / server_time
rho = lambd / mu

L_system_mean_an = rho / (1 - rho)
L_system_std_an = math.sqrt(rho / ((1-rho)**2))
L_queue_mean = rho**2 / (1-rho)

print(L_system_mean_an)
print(L_system_std_an)

L_system_an = np.random.normal(loc=L_system_mean_an, scale=L_system_std_an, size=10000)
solutions = pd.DataFrame(L_system_an, columns=['value'])
solutions = solutions.assign(variable='L_system_an')
solutions.insert(0, 'index', range(0, 0 + len(solutions)))

outcomes_df = pd.concat([outcomes_df, solutions])
print(outcomes_df)





# ## Plotting
fig, ax = plt.subplots()
to_plot = ['L_system', 'L_system_an', 'L_queue']
sns.boxplot(data=outcomes_df[outcomes_df["variable"].isin(to_plot)], x='variable', y='value', orient='v', ax=ax)
ax.grid()


plt.show()











