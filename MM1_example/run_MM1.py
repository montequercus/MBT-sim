from MM1 import *
import pandas as pd
from scipy import stats
# import unittest
#
# class Testing(unittest.TestCase):
#     def start_queue_length(self):
#         env.trace()
#
# def start_queue_length():
#     print(env.trace())

def print_levels(system, servers):
    print("Mean values of results:")
    print(f"{env.now():.3f}. L: Number of items in 'system': {system.length.mean():.3f}")
    print(f"{env.now():.3f}. L_q: Number of items in requesters of 'servers': {servers.requesters().length.mean():.3f}")
    print(f"{env.now():.3f}. L_s: Number of items in claimers of 'servers': {servers.claimers().length.mean():.3f}")
    print(f"{env.now():.3f}. W_q: Length of stay in requesters of 'servers': {servers.requesters().length_of_stay.mean():.3f}")
    print(f"{env.now():.3f}. W_s: Length of stay in claimers of 'servers': {servers.claimers().length_of_stay.mean():.3f}")

## Time 0: Check if elements have been made

env.run(till=100000)

rho = 1/2

L_system_dict = {
            "data": system.length.tx()[1],
            "mean": system.length.mean(),
            "mean analytical": rho / (1 - rho)
        }

# Significance testing
[t_value, p_value] = stats.ttest_1samp(L_system_dict['data'], popmean=L_system_dict['mean analytical'])

print(t_value)

system.print_statistics()
print_levels(system,servers)




# requesters_creation_times = [] # Initialize list
# for entity in servers.requesters():
#     creation_time = entity.creation_time
#     requesters_creation_times.append(requesters_creation_times)
# print(requesters_creation_times)

## Advance time to first event after t=0
# env.step()
# print_levels()

## Advance time to next event
# env.step()
# print_levels()

# env.run(till=150)

# if __name__ == '__main__':
#     unittest.main(argv=['ignored', '-v', 'Testing.test_string'], exit=False)