import unittest
import numpy as np
from warnings import warn
import importlib
from scipy import stats
import salabim as sim
import test
import time

import os
import sys

## Add parent directory to path
parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent_dir)
import MM1_new as MM1 # Import SUT from parent folder

## Setting: Test statistics in 'tearDownModel' or not. Set to False when multiple replications are to be performed

def setUpRun(data):
    # Reload SUT for new replication
    importlib.reload(MM1)

def advance_and_update_data(self, data):
    """
    Advance Salabim's simulation time to the next scheduled event.
    Update graph data that is used in abstract model for guards.
    Update data in memory list that are used in this test script.
    """
    # Advance SUT to next event
    MM1.env.step()

    # Update graph data
    data["t"] = MM1.env.now()  # time
    data["q"] = MM1.clerks.requesters().length()  # queue length
    num_in_system = MM1.clerks.requesters().length() + MM1.clerks.claimers().length() # Total number of entities in system
    data["s"] = num_in_system

    # Update memories for further asserts
    self.mem_num_in_system.append(num_in_system)
    self.mem_num_in_system = self.mem_num_in_system[-2:]  # Keep last two entries
    self.mem_num_in_service.append(MM1.clerks.claimers().length())  # Number of entities in service
    self.mem_num_in_service = self.mem_num_in_service[-2:]  # Keep last two entries

    # Deal with TCP/IP problem
    self.num_steps += 1 # Count number of time advances across AltWalker runs
    if self.num_steps == 1000:
        warn("120 second pause in execution starting.")
        time.sleep(121) # Pause execution for more than 120 seconds
        self.num_steps = 0 # Reset num_steps counter
    data['n_advances'] = self.num_steps

class MM1_FIFO(unittest.TestCase):
    def setUpModel(self, data):
        ## Initialize parameters, that were passed to graph from test execution script
        self.seed = int(data['seed'])
        self.iat = float(data['iat'])
        self.server_time = float(data['server_time'])

        ## Initialize SUT objects with new parameter values
        importlib.reload(MM1)
        MM1.inter_arrival_time_dis = sim.Exponential(self.iat)
        MM1.service_duration_dis = sim.Exponential(self.server_time)
        MM1.env.random_seed(self.seed)
        MM1.ClientGenerator()

        # Initialize memory lists used for asserts
        self.mem_num_in_system = [] # Number of entities in 'system'
        self.mem_num_in_service = [] # Number of entities in 'claimers' queue of 'servers'

        # Warn if steady-state will likely not be reached
        if self.server_time >= self.iat:
            rho = self.server_time / self.iat
            msg = f"setUpModel. Given the input parameters, 'rho' is too high: rho = {rho:.2f} >= 1. The system is therefore likely not stable. \n"
              #    f"Inter-arrival time = {self.iat:.2f}, server time = {self.server_time:.2f}"
            warn(msg)


        # Debugging: count AltWalker steps
        self.num_steps = int(data['n_advances']) # Take from previous test run

    def tearDownModel(self, data):
        """
        End of model run. Get statistics from end result, and compare to analytical solution.
        Pass verdicts to test execution script via graph data.
        """
        # Constants for analytical solutions
        lambd = 1 / self.iat
        mu = 1 / self.server_time
        rho = lambd / mu  # Utilization percentage of server

        # Analytical solutions
        L_system_an = rho / (1 - rho) if rho != 1 else float('inf')
        L_queue_an = (rho**2) / (1 - rho) if rho !=1 else float('inf')
        W_system_an = 1 / (mu - lambd) if mu != lambd else float('inf')
        W_queue_an =  rho / (mu - lambd) if mu != lambd else float('inf')

        # Data points, mean values, and analytical solution for level monitors
        L_system = {
            "name": "L: Number of items in system",
            "data": MM1.clerks.requesters().length.tx()[1] + MM1.clerks.claimers().length.tx()[1],
            "mean": MM1.clerks.requesters().length.mean() + MM1.clerks.claimers().length.mean(), # Time-average number
            "mean analytical": L_system_an
        }
        L_queue = {
            "name": "L_q: Number of items in queue (requesters)",
            "data": MM1.clerks.requesters().length.tx()[1],
            "mean": MM1.clerks.requesters().length.mean(), # Time-average
            "mean analytical": L_queue_an,
        }
        W_system = { # Time in system
            "name": "W: Time in system",
            "data": MM1.clerks.requesters().length_of_stay.tx()[1] + MM1.clerks.claimers().length_of_stay.tx()[1],
            "mean": MM1.clerks.requesters().length_of_stay.mean() + MM1.clerks.claimers().length_of_stay.mean(),
            "mean analytical": W_system_an,
        }
        W_queue = {
            "name": "W_q: Time in queue (requesters)",
            "data": MM1.clerks.requesters().length_of_stay.tx()[1],
            "mean": MM1.clerks.requesters().length_of_stay.mean(),
            "mean analytical": W_queue_an,
        }

        self.assertGreaterEqual(W_system['mean'], 0)
        self.assertGreaterEqual(L_system['mean'], 0)

        ## Get accepted deviations for this experiment
        accepted_deviation_occupancy = float(data['d_rho'])
        accepted_deviation_delta_relative = float(data['d_delta_relative'])

        ## Little's law
        delta = abs(W_system['mean'] - L_system['mean'] / lambd)
        delta_relative = (delta / W_system['mean']) * 100
        delta_relative_verdict = 'passed'
        if rho < 1 and delta_relative > accepted_deviation_delta_relative:
            msg = f"tearDownModel. Deviation from Little's law is too high: (W - L / lambda) = {delta:.2f}, or {delta_relative:.2f} % of W. Max. deviation is {accepted_deviation_delta_relative}. \n" f"W = {W_system['mean']:.2f}, L = {L_system['mean']:.2f}, lambda = {lambd:.2f}."
            warn(msg)
            delta_relative_verdict = 'failed'

        ## Occupancy compared to analytical solution
        occupancy_mean = MM1.clerks.occupancy.mean()
        occupancy_deviation_relative = abs((rho - occupancy_mean) / rho) * 100
        occupancy_verdict = 'passed'
        if rho < 1 and occupancy_deviation_relative > accepted_deviation_occupancy:
            msg = f"tearDownModel. Difference between mean occupancy and analytical solution is too high: (|rho - occupancy| / rho) = {occupancy_deviation_relative:.4f} % > {accepted_deviation_occupancy} %. \n" \
                  f"Occupancy = {occupancy_mean:.4f}, analytical   solution for rho = {rho:.4f}"
            warn(msg)
            occupancy_verdict = 'failed'

        msg = f"End of run. t = {MM1.env.now():.2f}. Result: occupancy = {occupancy_mean:.4f}. \n Number of time advances done: {self.num_steps}"
        warn(msg)

        ## Send results of runs to test execution script
        data['occupancy_mean'] = occupancy_mean
        data['occupancy_deviation_relative'] = occupancy_deviation_relative
        data['occupancy_verdict'] = occupancy_verdict
        data['delta'] = delta
        data['delta_relative'] = delta_relative
        data['delta_relative_verdict'] = delta_relative_verdict
        data['t_end_exact'] = MM1.env.now() # Exact t_end will differ from input parameter t_end


    def v_NoStepYet(self):
        """
        Start of model. There should be no entities yet, Requesters should be an empty queue.
        Assumption: all Client instances created by ClientGenerator succeed to enter requesters.
        """
        # Check if time is actually zero
        self.assertEqual(MM1.env.now(), 0)

        # Number of entities in queues
        self.assertEqual(MM1.clerks.requesters().length(), 0)
        self.assertEqual(MM1.clerks.claimers().length(), 0)

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
        data["q"] = MM1.clerks.requesters().length()

        # Update memories for further asserts
        self.mem_num_in_system.append(MM1.clerks.requesters().length() + MM1.clerks.claimers().length())
        self.mem_num_in_system = self.mem_num_in_system[-2:] # Keep last 2 entries

        # Asserts for when second time advance has been executed:
        if self.bool_second_advance:
            # First entity should be in the MM1.system
            self.assertEqual(self.mem_num_in_system[-1], 1)
            # First entity should claim Resource immediately
            self.assertEqual(MM1.clerks.claimers().length(), 1)
            self.assertEqual(MM1.clerks.requesters().length(), 0)

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

    def e_OneInQueue(self, data):
        """
        DO NOT advance time in SUT.
        Guards: q==1 (one in queue); t>0
        """
        msg = f"One new entity joins queue, at first event with time t > 0 \n " \
              f"t = {MM1.env.now()}, q = {data['q']}, s = {data['s']}"
        warn(msg)

    def e_MultipleInQueue(self, data):
        """
        DO NOT advance time in SUT.
        Guards: q>1 (multiple in queue); t>0
        """
        msg = f"Multiple new entities join queue, at first event with time > 0 \n" \
              f"t = {MM1.env.now()}, q = {data['q']}, s = {data['s']}"

    def v_NoneInQueue(self, data):
        """
        Do asserts for when queue is empty.
        The number of entities in the system may only have changed by 1.
        There may be 0 or 1 entities in the system.
        If there is an entity in the system, it should be in service.
        """
        # Double check if guard has worked correctly
        self.assertEqual(MM1.clerks.requesters().length(), 0) # Queue is empty
        self.assertEqual(int(data["q"]), 0) # Queue is empty according to graph data

        # Get change in number of entities in system
        delta_num_in_system = np.diff(self.mem_num_in_system)
        self.assertLessEqual(abs(delta_num_in_system), 1) # Difference may only be 1 or 0 for one event

        # System may have 0 or 1 entities, when none are in queue
        self.assertLessEqual(self.mem_num_in_system[-1], 1)


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
        self.assertEqual(MM1.clerks.requesters().length(), 1) # Queue contains one entity
        self.assertEqual(int(data["q"]), 1) # Queue contains one entity according to graph data
        self.assertEqual(MM1.clerks.claimers().length(), 1)

        # Get change in number of entities in system
        delta_num_in_system = np.diff(self.mem_num_in_system)
        self.assertLessEqual(abs(delta_num_in_system), 1) # Difference may only be 1 or 0

        # System may have 1 or 2 entities
        # self.assertTrue(1 <= self.mem_num_in_system[-1] <= 2)

        # If there was no entity in service in previous step
        if self.mem_num_in_service[-2] == 0:
            # Then one entity should be in service now
            self.assertEqual(MM1.clerks.claimers().length(), 1)

        # If there is an entity in service
        if MM1.clerks.claimers().length() == 1:
            # Timestamp of entity in service should be lower than that of entity in queue
            ts_in_service = MM1.clerks.claimers().head().creation_time()
            ts_in_queue = MM1.clerks.requesters().head().creation_time()
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
        self.assertGreater(MM1.clerks.requesters().length(), 1) # Queue contains multiple entities
        self.assertGreater(int(data["q"]), 1 ) # Queue contains multiple entities according to graph data

        # Get change in number of entities in system
        delta_num_in_system = np.diff(self.mem_num_in_system)
        self.assertLessEqual(abs(delta_num_in_system), 1) # Difference may only be 1 or 0

        # System may have 2 or more entities
        self.assertGreaterEqual(self.mem_num_in_system[-1], 2)

        # If there was no entity in service in previous step
        if self.mem_num_in_service[-2] == 0:
            # Then one entity should be in service now
            self.assertEqual(MM1.clerks.claimers().length(), 1)

            # If there is an entity in service
            if MM1.clerks.claimers().length() == 1:
                # Timestamp of entity in service should be lower than that of entity in queue
                ts_in_service = MM1.clerks.claimers().head().creation_time()
                ts_in_queue = MM1.clerks.requesters().head().creation_time()
                self.assertLess(ts_in_service, ts_in_queue)

        # Creation time of requesters in queue should follow FIFO logic
        requester_creation_times = [entity.creation_time() for entity in MM1.clerks.requesters()]
        delta_creation_times = np.diff(requester_creation_times) # Differences between creation times
        # FIFO: See if all differences in creation times are positive
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
        msg = f"e_MultipleJoinQueue. Queue length has increased from 0 to {MM1.clerks.requesters().length()} after a single event."
        warn(msg)

    def e_AllLeaveQueue(self):
        """"
        v_MultipleInQueue --> v_NoneInQueue
        Guard: q==0
        """
        msg = f"e_AllLeaveQueue. Queue length() has decreased to 0 after a single event. There were {self.mem_num_in_system[-2]} entities in the system after the previous event."
        warn(msg)

class MM1_FIFO_with_s(MM1_FIFO): # Inherits all test functions from MM1_FIFO
    ## Override methods for some tests
    def v_NoneInQueue(self, data):
        """
        Do asserts for when queue is empty, and there is one entity in system
        The number of entities in the system may only have changed by 1.
        There may only 1 entity in the system, which should be in service.
        """
        # Double check if guard has worked correctly
        self.assertEqual(MM1.clerks.requesters().length(), 0) # Queue is empty
        self.assertEqual(int(data["q"]), 0) # Queue is empty according to graph data

        # Get change in number of entities in system
        delta_num_in_system = np.diff(self.mem_num_in_system)
        self.assertLessEqual(abs(delta_num_in_system), 1) # Difference may only be 1 or 0 for one event

        # System may have only 1 entity
        self.assertEqual(self.mem_num_in_system[-1], 1)

        # Entity in system must be in service
        self.assertEqual(MM1.clerks.claimers().length(), 1, msg="Only entity in system is not in service.")

        # Advance time and update data
        advance_and_update_data(self, data)

    def v_NoneInSystem(self,data):
        """
        Do asserts for when system is empty.
        The number of entities in the system may have only changed by 1, compared to the previous step.
        """
        # Double check if guard has worked correctly
        self.assertEqual(MM1.clerks.requesters().length(), 0)
        self.assertEqual(MM1.clerks.claimers().length(), 0)

        # Get change in number of entities in system
        delta_num_in_system = np.diff(self.mem_num_in_system)
        self.assertLessEqual(abs(delta_num_in_system), 1)  # Difference may only be 1 or 0 for one event

        # Advance time and update data
        advance_and_update_data(self, data)

    ## New tests: from v_NoneInSystem
    def e_NewToService(self):
        """
        v_NoneInService --> v_NoneInQueue
        Guards: q==0 && s==1
        """
        pass

    def e_NewToQueue(self, data):
        """
        v_NoneInService --> v_OneInQueue
        Guards: q==1
        """
        msg = f"One new entity joins queue, while system was empty." \
              f"t = {MM1.env.now()}, q = {data['q']}, s = {data['s']}"
        warn(msg)

    def e_MultipleNewToQueue(self, data):
        """
        v_NoneInService --> v_MultipleInQueue
        Guards: q>1
        """
        msg = f"Multiple new entities join queue, while system was empty." \
              f"t = {MM1.env.now()}, q = {data['q']}, s = {data['s']}"
        warn(msg)

    def e_selfNone(self):
        """
        self-edge for v_NoneInService
        Guards: s==0
        """
        pass

    ## New tests: to v_NoneInSystem
    def e_NoneInSystem(self, data):
        """
        v_TimeZero --> v_NoneInSystem
        Guards: t>0 && s==0
        """
        pass

    def e_LastLeavesService(self):
        """
        v_NoneInQueue --> v_NoneInSystem
        Guards: s==0
        """
        pass

    def e_QueuedLeavesSystem(self, data):
        """
        v_OneInQueue --> v_NoneInSystem
        Guards: s==0
        """
        msg = f"One entity was in queue, but all entities have left the system." \
              f"t = {MM1.env.now()}, q = {data['q']}, s = {data['s']}"
        warn(msg)

    def e_AllLeaveSystem(self, data):
        """
        v_MultipleInQueue --> v_NoneInSystem
        Guards: s==0
        """
        msg = f"Multiple entities were in queue, but all entities have left the system." \
              f"t = {MM1.env.now()}, q = {data['q']}, s = {data['s']}"
        warn(msg)

class MM1_FIFO_with_s_and_fail(MM1_FIFO_with_s): # Inherits all test functions from MM1_FIFO_with_s
    ## New methods for new path elements
    def e_FailOrEnd(self):
        pass

    def v_FailOrEnd(self):
        """
        multiple source vertices possible
        Guard: t == 0 || t > t_end
        """
        ## Analytical solution
        occupancy_mean = MM1.clerks.occupancy.mean()
        pass

