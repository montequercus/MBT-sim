from MM1 import *
import unittest

class Testing(unittest.TestCase):
    def start_queue_length(self):
        env.trace()

def start_queue_length():
    print(env.trace())

def print_levels():
    print(f"{env.now():.3f}. Number of items in 'system' Queue: {system.length()}")
    print(f"{env.now():.3f}. Number of items in 'servers' Resource's requesters: {servers.requesters().length()}")
    print(f"{env.now():.3f}. Number of items in 'servers' Resource's claimers: {servers.claimers().length()}")

## Time 0: Check if elements have been made

env.print_info()
env.step()
print(env.now())
print(servers.claimers().head())
env.step()
print(env.now())
print(servers.claimers().head())
env.step()
print(env.now())
print(servers.claimers().head())
env.step()
print(env.now())
print(servers.claimers().head())

## Advance time to first event after t=0
# env.step()
# print_levels()

## Advance time to next event
# env.step()
# print_levels()

# env.run(till=150)

# if __name__ == '__main__':
#     unittest.main(argv=['ignored', '-v', 'Testing.test_string'], exit=False)