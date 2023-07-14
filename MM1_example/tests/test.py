import unittest
import numpy as np
import warnings
import importlib
from scipy import stats

import sys
# Add parent folder to root
# from ... import MM1_example
sys.path.append("C:\\Users\\Ferd\\Desktop\\Thesis\\MBT-sim\\MM1_example")
import MM1 # Import SUT from parent folder

## Setting: Test statistics in 'tearDownModel' or not. Set to False when multiple replications are to be performed

def setUpRun():
    # Reload SUT for new replication
    importlib.reload(MM1)

def tearDownRun():
    """
    Reset all objects of Salabim model for next replication
    """
    # del env, servers, system, server_time, iat
    # env.reset_now() # Reset time
    # servers.reset_monitors()
    # system.reset_monitors()
    # print(system.head()) # See if there was an entity left in Queue instance
    # servers.requesters().clear() # Remove all from this Queue
    # servers.claimers().clear() # Remove all from this Queue
    # system.clear() # Remove all from this Queue
    # salabim.reset()
    pass

def advance_and_update_data(self, data):
    """
    Advance Salabim's simulation time to the next scheduled event.
    Update graph data that is used in abstract model for guards.
    Update data in memory list that are used in this test script.
    """
    # Advance SUT to next event
    MM1.env.step()

    # Update graph data
    data["t"] = MM1.env.now() # time
    data["q"] = MM1.servers.requesters().length() # queue length

    # Update memories for further asserts
    self.mem_num_in_system.append(MM1.system.length()) # Number of entities in system
    self.mem_num_in_system = self.mem_num_in_system[-2:] # Keep last two entries
    self.mem_num_in_service.append(MM1.servers.claimers().length()) # Number of entities in service
    self.mem_num_in_service = self.mem_num_in_service[-2:] # Keep last two entries

def ttest_analytical(self, result, alpha, bool_assert_statistic):
    """
    Perform t-test on dictionary that contains data and analytical mean.
    self: associated test class
    result: dict
    alpha: float
    bool_assert_statistic: bool. True: assert will be used, AltWalker test fails if t-test fails. False: No asserts will be used. Use this option when running replications.
    """
    [result['t statistic'], result['p value']] = stats.ttest_1samp(result['data'], popmean=result['mean many runs'])
    if bool_assert_statistic:
        self.assertGreater(result['p value'], alpha,
                           msg = f"Test of mean of {result['name']} has rejected the hypothesis. \n time: {MM1.env.now()} \n p-value: {result['p value']} \n alpha: {alpha} \n calculated mean: {result['mean']} \n analytical mean: {result['mean analytical']}")
    else:
        print(f"Statistics of run for: {result['name']}. \n calculated mean: {result['mean']} \n analytical mean: {result['mean analytical']}")

class MM1_FIFO(unittest.TestCase):
    def setUpModel(self):
        # Initialize memory lists used for asserts
        self.mem_num_in_system = [] # Number of entities in 'system'
        self.mem_num_in_service = [] # Number of entities in 'claimers' queue of 'servers'

        # Warn if steady-state will likely not be reached
        if MM1.server_time >= MM1.iat:
            warnings.warn(f"Queue is likely not stable, given the conditions: inter-arrival time = {MM1.iat}, server_time = {MM1.server_time} ")

    def tearDownModel(self):
        """
        End of model run. Get statistics from end result, and compare to analytical solution.
        """

        # Setting: confidence level
        alpha = 0.05 # Confidence level

        # Constants for analytical solutions
        lambd = 1 / MM1.iat
        mu = 1 / MM1.server_time
        rho = lambd / mu  # Utilization percentage of server

        # Data points, mean values, and analytical solution for level monitors
        L_system = {
            "name": "L: Number of items in system",
            "data": MM1.system.length.tx()[1],
            "mean": MM1.system.length.mean(), # Time-average
            "mean analytical": rho / (1 - rho),
            "mean many runs": 1
        }
        L_queue = {
            "name": "L_q: Number of items in queue (requesters)",
            "data": MM1.servers.requesters().length.tx()[1],
            "mean": MM1.servers.requesters().length.mean(), # Time-average
            "mean analytical": (rho**2) / (1 - rho),
            "mean many runs": 0.5
        }
        W_system = { # Time in system
            "name": "W: Time in system",
            "data": MM1.system.length_of_stay.tx()[1],
            "mean": MM1.system.length_of_stay.mean(),
            "mean analytical": 1 / (mu - lambd),
            "mean many runs": 10
        }
        W_queue = {
            "name": "W_q: Time in queue (requesters)",
            "data": MM1.servers.requesters().length_of_stay.tx()[1],
            "mean": MM1.servers.requesters().length_of_stay.mean(),
            "mean analytical": rho / (mu - lambd),
            "mean many runs": 5
        }

        # Select whether to assert (True) or only print outcomes (False)
        bool_assert_statistic = False

        # Significance testing
        print(MM1.env.now())
        ttest_analytical(self, L_system, alpha, bool_assert_statistic)
        ttest_analytical(self, L_queue, alpha, bool_assert_statistic)
        ttest_analytical(self, W_system, alpha, bool_assert_statistic)
        ttest_analytical(self, W_queue, alpha, bool_assert_statistic)

    def v_NoStepYet(self):
        """
        Start of model. There should be no entities yet, 'system' should be an empty queue.
        Assumption: all Client instances created by ClientGenerator succeed to enter 'system'.
        """
        # Check if time is actually zero
        self.assertEqual(MM1.env.now(), 0)

        # Number of entities in system
        self.assertEqual(MM1.system.length(), 0)

    def e_AdvanceFirst(self, data):
        """
        Advance to first event, which is at time 0.000
        """
        # Remember that second advance has not been executed (for v_TimeZero)
        self.bool_second_advance = False
        # Advance to first event
        advance_and_update_data(self, data)

    def v_TimeZero(self, data):
        """
        Do checks that need to be done when time is 0.
        See if ClientGenerator has made a Client
        Assumption: all Client instances created by ClientGenerator succeed to enter 'system'.
        """
        # Update queue length in graph data
        data["q"] = MM1.servers.requesters().length()

        # Update memories for further asserts
        self.mem_num_in_system.append(MM1.system.length())
        self.mem_num_in_system = self.mem_num_in_system[-2:]

        # Asserts for when second time advance has been executed:
        if self.bool_second_advance:
            # First entity should be in the MM1.system
            self.assertEqual(MM1.system.length(), 1)
            # First entity should claim Resource immediately
            self.assertEqual(MM1.servers.claimers().length(), 1)
            queue_length = MM1.servers.requesters().length()
            self.assertEqual(queue_length, 0)

        # Advance time and update data
        advance_and_update_data(self, data)


    def e_TimeStillZero(self):
        """
        Guard: t==0
        self-edge of 'v_TimeZero'
        No time advancement on this edge.
        """
        # Remember that second advance has been executed
        self.bool_second_advance = True

    def e_NoneInQueue(self):
        """
        DO NOT advance time in SUT.
        Guards: q==0 (empty queue); t>0
        """

    def e_OneInQueue(self):
        """
        DO NOT advance time in SUT.
        Guards: q==1 (one in queue); t>0
        """
        pass

    def e_MultipleInQueue(self):
        """
        DO NOT advance time in SUT.
        Guards: q>1 (multiple in queue); t>0
        """
        pass

    def v_NoneInQueue(self, data):
        """
        Do asserts for when queue is empty.
        The number of entities in the system may only have changed by 1.
        There may be 0 or 1 entities in the system.
        If there is an entity in the system, it should be in service.
        """
        # Double check if guard has worked correctly
        self.assertEqual(MM1.servers.requesters().length(), 0) # Queue is empty
        self.assertEqual(int(data["q"]), 0) # Queue is empty according to graph data

        # Get change in number of entities in system
        delta_num_in_system = np.diff(self.mem_num_in_system)
        # Difference may only be 1 or 0
        self.assertLessEqual(abs(delta_num_in_system), 1)

        # System may have 0 or 1 entities
        self.assertLessEqual(MM1.system.length(), 1)

        # If there is an entity in the system
        if MM1.system.length() == 1:
            # Entity must be in service, since none are in queue
            self.assertEqual(MM1.servers.claimers().length(), 1)

        # DEBUG
        # print(f"Time:{MM1.env.now()}")
        # print(f"System:{MM1.system.length()}")
        # print(f"Requesters:{MM1.servers.requesters().length()}")
        # print(f"Claimers:{MM1.servers.claimers().length()}")

        # Advance time and update data
        advance_and_update_data(self, data)

    def v_OneInQueue(self, data):
        """
        Do asserts for when there is one entity in queue.
        Again, the number of entities in the system may only have changed by 1.
        There may be 1 or 2 entities in the system now.
        Again, if there was no entity in service in the previous step, there should be one now.
        If an entity is in service, its time of creation should be lower than that of the entity in the queue.
        """
        # Double check if guard has worked correctly
        self.assertEqual(MM1.servers.requesters().length(), 1)  # Queue contains one entity
        self.assertEqual(int(data["q"]), 1)  # Queue contains one entity according to graph data

        # Get change in number of entities in system
        delta_num_in_system = np.diff(self.mem_num_in_system)
        # Difference may only be 1 or 0
        self.assertLessEqual(abs(delta_num_in_system), 1)

        # System may have 1 or 2 entities
        self.assertTrue(1 <= MM1.system.length() <= 2)

        # If there was no entity in service in previous step
        if self.mem_num_in_service[-2] == 0:
            # Then one entity should be in service now
            self.assertEqual(MM1.servers.claimers().length(), 1)

        # If there is an entity in service
        if MM1.servers.claimers().length() == 1:
            # Timestamp of entity in service should be lower than entity in queue
            ts_in_service = MM1.servers.claimers().head().creation_time()  # Timestamp of entity in service
            ts_in_queue = MM1.servers.requesters().head().creation_time() # Timestamp of entity in queue
            self.assertLess(ts_in_service, ts_in_queue)

        # Advance time and update data
        advance_and_update_data(self, data)

    def v_MultipleInQueue(self, data):
        """
        Do asserts for when there is one entity in queue.
        Again, the number of entities in the system may only have changed by 1.
        There may be 2 or more entities in the system now.
        Again, if there was no entity in service in the previous step, there should be one now.
        Again, if an entity is in service, its time of creations should be lower than that of the entity in the queue.
        The queue must be in FIFO order.
        """
        # Double check if guard has worked correctly
        self.assertGreater(MM1.servers.requesters().length(), 1)  # Queue contains multiple entities
        self.assertGreater(int(data["q"]), 1)  # Queue contains multiple entities according to graph data

        # Get change in number of entities in system
        delta_num_in_system = np.diff(self.mem_num_in_system)
        # Difference may only be 1 or 0
        self.assertLessEqual(abs(delta_num_in_system), 1)

        # System may have 2 or more entities
        self.assertGreaterEqual(MM1.system.length(), 2)

        # If there was no entity in service in previous step
        if self.mem_num_in_service[-2] == 0:
            # Then one entity should be in service now
            self.assertEqual(MM1.servers.claimers().length(), 1)

            # If there is an entity in service
            if MM1.servers.claimers().length() == 1:
                # Timestamp of entity in service should be lower than entity in queue
                ts_in_service = MM1.servers.claimers().head().creation_time()  # Timestamp of entity in service
                ts_in_queue = MM1.servers.requesters().head().creation_time()  # Timestamp of entity in queue
                self.assertLess(ts_in_service, ts_in_queue)

        # Creation time of requesters in queue
        requesters_creation_times = [entity.creation_time() for entity in MM1.servers.requesters()]
        delta_creation_times = np.diff(requesters_creation_times) # Differences between values
        # FIFO: See if all difference in values are positive
        self.assertTrue(all(x>=0 for x in delta_creation_times))

        # Advance time and update data
        advance_and_update_data(self, data)

    def e_self0(self):
        """
        Self-edge of 'v_NoneInQueue'.
        Guard: q==0
        """
        pass

    def e_self1(self):
        """
        Self-edge of 'v_OneInQueue'.
        Guard: q==1
        """
        pass

    def e_self2(self):
        """
        Self-edge of 'v_MultipleInQueue'.
        Guard: q>1
        """
        pass

    def e_OneJoinsEmptyQueue(self):
        """
        v_NoneInQueue --> v_OneInQueue
        Guard: q==1
        """
        pass

    def e_LastLeavesQueue(self):
        """
        v_OneInQueue --> v_NoneInQueue
        Guard: q==0
        """
        pass

    def e_AnotherJoinsQueue(self):
        """
        v_OneInQueue --> v_MultipleInQueue
        Guard: q>1
        """
        pass

    def e_ForelastLeavesQueue(self):
        """
        v_MultipleInQueue --> v_OneInQueue
        Guard: q==1
        """
        pass

    def e_MultipleJoinQueue(self):
        """"
        v_NoneInQueue --> v_MultipleInQueue
        Guard: q>1
        """
        warnings.warn(f"Queue length has increased from 0 to {MM1.servers.requesters().length()} during one event.")


    def e_AllLeaveQueue(self):
        """"
        v_MultipleInQueue --> v_NoneInQueue
        Guard: q==0
        """
        warnings.warn(f"Queue length() has decreased to 0 in event. There were {self.mem_num_in_system[-2]} entities in the system after the previous event.")

