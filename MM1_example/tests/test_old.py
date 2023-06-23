import unittest
import numpy as np

import sys
# Add the ptdraft folder path to the sys.path list
sys.path.append('C:/Users/Ferd/Desktop/Thesis/Testing_tools/Salabim')

from MM1 import *

def advance_and_update_data(self, data):
    """
    Update graph data that is used in abstract model for guards
    """
    # Advance SUT to next event
    env.step()

    # Update graph data
    data["t"] = env.now() # time
    data["q"] = servers.requesters().length # queue length

    # Update memories for further asserts
    self.mem_num_in_system.append(system.length)
    self.mem_num_in_system = self.mem_num_in_system[-2:]

class MM1_FIFO(unittest.TestCase):
    def setUpModel(self):
        # Initialize memories used for asserts
        self.mem_num_in_system = [] # Number of entities in 'system'

    def tearDownModel(self):
        pass

    def v_NoStepYet(self):
        """
        Start of model. There should be no entities yet, 'system' should be an empty queue.
        Assumption: all Client instances created by ClientGenerator succeed to enter 'system'.
        """
        # Check if time is actually zero
        self.assertEqual(env.now(), 0)

        # Number of entities in system
        self.assertEqual(system.length, 0)

    def e_AdvanceFirst(self, data):
        """
        Advance to first event, which is at time 0.000
        """
        advance_and_update_data(data)
        # Remember that second advance has not been executed (for v_TimeZero)
        self.bool_second_advance = False

    def v_TimeZero(self, data):
        """
        Do checks that need to be done when time is 0. Otherwise, go to vertex with asserts for t>0.
        See if ClientGenerator has made a Client
        Assumption: all Client instances created by ClientGenerator succeed to enter 'system'.
        """
        # Update queue length in graph data
        data["q"] = servers.requesters().length

        # Update memories for further asserts
        self.mem_num_in_system.append(system.length)
        self.mem_num_in_system = self.mem_num_in_system[-2:]

        # Do asserts from this vertex only if time is 0.
        if env.now == 0:
            # First entity should be in system
            self.assertEqual(system.length, 1)

            # First entity should claim Resource immediately
            self.assertEqual(servers.claimers().length, 1)
            queue_length = servers.requesters().length
            self.assertEqual(queue_length, 0)

    def e_TimeStillZero(self, data):
        """
        Advance time in SUT
        Guard: t==0
        """
        advance_and_update_data(data)
        # Remember that second advance has been executed
        self.bool_second_advance = True

    def e_NoneInQueue(self, data):
        """
        DO NOT advance time in SUT.
        Guards: q==0 (empty queue); t>0
        """
        pass

    def e_OneInQueue(self, data):
        """
        DO NOT advance time in SUT.
        Guards: q==1 (one in queue); t>0
        """
        pass

    def e_MultipleInQueue(self, data):
        """
        DO NOT advance time in SUT.
        Guards: q>1 (multiple in queue); t>0
        """
        pass

    def v_NoneInQueue(self, data):
        """
        Do necessary checks for when queue was empty.
        There may now be 0 or 1 entities in the queue.
        The server may be empty, but only if there are no entities in the system.
        The number of entities in the system can only have changed with one.
        """
        # Update memories for further asserts
        self.mem_num_in_system.append(system.length)
        self.mem_num_in_system = self.mem_num_in_system[-2:]

        # Change in number of entities in system
        delta_num_in_system = np.diff(self.mem_num_in_system)
        self.assertLessEqual(abs(delta_num_in_system), 1)

        # Number of entities in queue
        self.assertLessEqual(servers.requesters().length, 1)

        # Number of entities in service
        if servers.claimers().length == 0:
            # If none are in service
            self.assertEqual(system.length(), 0,
                             msg = "No claimers for 'servers', while there are clients in 'system'.")

        # Update queue length in graph data
        data["q"] = servers.requesters().length


    def v_OneInQueue(self, data):
        """
        Do necessary checks for when one was in queue.
        The number of elements in the system may only have changed with one.
        There may now be 0, 1, or 2 entities in the queue.
        The queue must be in FIFO order.
        """
        # Update memories for further asserts
        self.mem_num_in_system.append(system.length)
        self.mem_num_in_system = self.mem_num_in_system[-2:]

        # Change in number of entities in system
        delta_num_in_system = np.diff(self.mem_num_in_system)
        self.assertLessEqual(abs(delta_num_in_system), 1)

        # Number of entities in queue
        self.assertLessEqual(servers.requesters().length, 2)

        # Number of entities in service
        # self.assertEqual(servers.claimers().length == 1)

        # FIFO: length of stay in requesters queue
        requesters_length_of_stay = [entity.length_of_stay for entity in servers.requesters()] # List of lengths of stay
        delta_length_of_stay = np.diff(requesters_length_of_stay)
        # See if all deltas are either all positive or all negative
        bool_deltas_positive = all(x>=0 for x in delta_length_of_stay)
        bool_deltas_negative = all(x<=0 for x in delta_length_of_stay)
        self.assertTrue(bool_deltas_positive or bool_deltas_negative)

        # Timestamp of entity in service should be lower than those in queue
        ts_in_service = servers.claimers().head().creation_time() # Timestamp
        self.assertTrue(all(x > ts_in_service for x in servers.claimers()))

        # Update queue length in graph data
        data["q"] = servers.requesters().length

    def v_MultipleInQueue(self, data):
        """
        Do necessary checks for when multiple were in queue
        The number of elements in the system may only have changed with one.
        There may now be 0, 1, or 2 entities in the queue.
        ~~There should be an element in service.~~
        The queue must be in FIFO order.
        """
        # Update memories for further asserts
        self.mem_num_in_system.append(system.length)
        self.mem_num_in_system = self.mem_num_in_system[-2:]

        # Change in number of entities in system
        delta_num_in_system = np.diff(self.mem_num_in_system)
        self.assertLessEqual(abs(delta_num_in_system), 1)

        # Number of entities in queue
        self.assertGreater(servers.requesters().length, 0)

        # Number of entities in service
        # self.assertEqual(servers.claimers().length == 0)

        # FIFO: length of stay in requesters queue
        requesters_length_of_stay = [entity.length_of_stay for entity in
                                     servers.requesters()]  # List of lengths of stay
        delta_length_of_stay = np.diff(requesters_length_of_stay) # Differences between values
        # See if all deltas are either all positive or all negative
        bool_deltas_positive = all(x >= 0 for x in delta_length_of_stay)
        bool_deltas_negative = all(x <= 0 for x in delta_length_of_stay)
        self.assertTrue(bool_deltas_positive or bool_deltas_negative)

        # Timestamp of entity in service should be lower than those in queue
        ts_in_service = servers.claimers().head().creation_time()  # Timestamp
        self.assertTrue(all(x > ts_in_service for x in servers.claimers()))

        # Update queue length in graph data
        data["q"] = servers.requesters().length

    def e_Advance0(self, data):
        """
        Advance from 'v_NoneInQueue'.
        Guard: q==0
        """
        advance_and_update_data(data)

    def e_Advance1(self, data):
        """
        Advance from 'v_OneInQueue'.
        Guard: q==1
        """
        advance_and_update_data(data)

    def e_Advance2(self, data):
        """
        Advance from 'v_MultipleInQueue'.
        Guard: q>1
        """
        advance_and_update_data(data)

    def e_AllLeaveQueue(self):
        """
        Advance from 'v_MultipleInQueue'.
        Guard: q==0
                """
    # Should raise a warning

    def e_AnotherJoinsQueue(self):
        pass

    def e_ForeLastLeavesQueue(self):
        pass

    def e_MultipleJoinQueue(self):
        pass
    # Should raise a warning

    def e_OneJoinsEmptyQueue(self):
        pass

    def e_OneLeavesQueue(self):
        pass

