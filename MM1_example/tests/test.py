import unittest
import numpy as np
import warnings

import sys
# Add parent folder to root
from ... import MM1_example
# Import the SUT simulation model
from MM1 import *

def advance_and_update_data(self, data):
    """
    Advance Salabim's simulation time to the next scheduled event.
    Update graph data that is used in abstract model for guards.
    Update data in memory list that are used in this test script.
    """
    # Advance SUT to next event
    env.step()

    # Update graph data
    data["t"] = env.now() # time
    data["q"] = servers.requesters().length() # queue length

    # Update memories for further asserts
    self.mem_num_in_system.append(system.length()) # Number of entities in system
    self.mem_num_in_system = self.mem_num_in_system[-2:] # Keep last two entries
    self.mem_num_in_service.append(servers.claimers().length()) # Number of entities in service
    self.mem_num_in_service = self.mem_num_in_service[-2:] # Keep last two entries

class MM1_FIFO(unittest.TestCase):
    def setUpModel(self):
        # Initialize memory lists used for asserts
        self.mem_num_in_system = [] # Number of entities in 'system'
        self.mem_num_in_service = [] # Number of entities in 'claimers' queue of 'servers'

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
        self.assertEqual(system.length(), 0)

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
        data["q"] = servers.requesters().length()

        # Update memories for further asserts
        self.mem_num_in_system.append(system.length())
        self.mem_num_in_system = self.mem_num_in_system[-2:]

        # Asserts for when second time advance has been executed:
        if self.bool_second_advance:
            # First entity should be in the system
            self.assertEqual(system.length(), 1)
            # First entity should claim Resource immediately
            self.assertEqual(servers.claimers().length(), 1)
            queue_length = servers.requesters().length()
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
        pass

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
        self.assertEqual(servers.requesters().length(), 0) # Queue is empty
        self.assertEqual(int(data["q"]), 0) # Queue is empty according to graph data

        # Get change in number of entities in system
        delta_num_in_system = np.diff(self.mem_num_in_system)
        # Difference may only be 1 or 0
        self.assertLessEqual(abs(delta_num_in_system), 1)

        # System may have 0 or 1 entities
        self.assertLessEqual(system.length(), 1)

        # If there is an entity in the system
        if system.length() == 1:
            # Entity must be in service, since none are in queue
            self.assertEqual(servers.claimers().length(), 1)

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
        self.assertEqual(servers.requesters().length(), 1)  # Queue contains one entity
        self.assertEqual(int(data["q"]), 1)  # Queue contains one entity according to graph data

        # Get change in number of entities in system
        delta_num_in_system = np.diff(self.mem_num_in_system)
        # Difference may only be 1 or 0
        self.assertLessEqual(abs(delta_num_in_system), 1)

        # System may have 1 or 2 entities
        self.assertTrue(1 <= system.length() <= 2)

        # If there was no entity in service in previous step
        if self.mem_num_in_service[-2] == 0:
            # Then one entity should be in service now
            self.assertEqual(servers.claimers().length(), 1)

        # If there is an entity in service
        if servers.claimers().length() == 1:
            # Timestamp of entity in service should be lower than entity in queue
            ts_in_service = servers.claimers().head().creation_time()  # Timestamp of entity in service
            ts_in_queue = servers.requesters().head().creation_time() # Timestamp of entity in queue
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
        self.assertGreater(servers.requesters().length(), 1)  # Queue contains multiple entities
        self.assertGreater(int(data["q"]), 1)  # Queue contains multiple entities according to graph data

        # Get change in number of entities in system
        delta_num_in_system = np.diff(self.mem_num_in_system)
        # Difference may only be 1 or 0
        self.assertLessEqual(abs(delta_num_in_system), 1)

        # System may have 2 or more entities
        self.assertGreaterEqual(system.length(), 2)

        # If there was no entity in service in previous step
        if self.mem_num_in_service[-2] == 0:
            # Then one entity should be in service now
            self.assertEqual(servers.claimers().length(), 1)

            # If there is an entity in service
            if servers.claimers().length() == 1:
                # Timestamp of entity in service should be lower than entity in queue
                ts_in_service = servers.claimers().head().creation_time()  # Timestamp of entity in service
                ts_in_queue = servers.requesters().head().creation_time()  # Timestamp of entity in queue
                self.assertLess(ts_in_service, ts_in_queue)

        # Length of stay in requesters queue
        requesters_length_of_stay = [entity.length_of_stay for entity in
                                     servers.requesters().as_list()]  # List of lengths of stay
        delta_length_of_stay = np.diff(requesters_length_of_stay)  # Differences between values
        # FIFO: See if all deltas are either all positive or all negative
        bool_deltas_positive = all(x >= 0 for x in delta_length_of_stay)
        bool_deltas_negative = all(x <= 0 for x in delta_length_of_stay)
        self.assertTrue(bool_deltas_positive or bool_deltas_negative)

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
        warnings.warn(f"Queue length has increased from 0 to {servers.requesters().length()} during one event.")


    def e_AllLeaveQueue(self):
        """"
        v_MultipleInQueue --> v_NoneInQueue
        Guard: q==0
        """
        warnings.warn(f"Queue length() has decreased to 0 in event. There were {self.mem_num_in_system[-2]} entities in the system after the previous event.")

