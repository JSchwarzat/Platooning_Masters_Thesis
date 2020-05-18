"""
This class extends the traci &  plexe methods.
"""

import os
import sys
import random

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
import traci
from CONSTANTS import DEBUG_HAPPINESS, HAPPINESS_TABLE_SIZE, NEW_SPAWNED, STANDARD_COLOR


class VehicleData:
    def __init__(self, id, desired_speed_factor=0):
        self.__id = id
        self.__floatID = int(id[2:]) + 1000
        self.__isLeader = False
        self.__platoonLeader = None
        self.__desiredPlatoonLeader = None
        self.__platoonMembers = []
        self.__desiredPlatoonSpeed = -1
        self.__posInPlatoon = None
        self.__state = NEW_SPAWNED
        self.__color = random.uniform(70, 255), random.uniform(70, 255), random.uniform(70, 255), 255
        self.__happiness_table = {}
        self.__neighbor_table_pos = 0
        self.__hasJoiner = False
        self.__hasLeaver = False
        self.__desired_speed_factor = desired_speed_factor
        self.__counter = 0
        self.__crash_counter = 0
        self.__neighbors = []
        self.__candidates = []
        self.__cache = []
        self.__from_another_platoon = False
        self.__old_happiness = 0

    """ ############################################################################
                                Methods for Monitoring
    ############################################################################ """

    def set_old_happiness(self, value):
        self.__old_happiness = value

    def get_old_happiness(self):
        return self.__old_happiness

    def is_from_another_platoon(self):
        return self.__from_another_platoon

    def set_from_another_platoon(self):
        self.__from_another_platoon = True

    def reset_from_another_platoon(self):
        self.__from_another_platoon = False

    def inc_crash_counter(self):
        self.__crash_counter += 1

    def get_crash_counter(self):
        return self.__crash_counter

    def reset_crash_counter(self):
        self.__crash_counter = 0

    """ ############################################################################
                                Joiner / Leaver Management
    ############################################################################ """

    def inc_counter(self):
        self.__counter += 1

    def get_counter(self):
        return self.__counter

    def reset_counter(self):
        self.__counter = 0

    def has_joiner(self):
        return self.__hasJoiner

    def set_joiner(self):
        self.__hasJoiner = True

    def reset_joiner(self):
        self.__hasJoiner = False

    def has_leaver(self):
        return self.__hasLeaver

    def set_leaver(self):
        self.__hasLeaver = True

    def reset_leaver(self):
        self.__hasLeaver = False

    """ ############################################################################
                                Platoon Related
    ############################################################################ """

    def add_platoon_member(self, member, pos=-1):
        if pos == -1:
            self.__platoonMembers.append(member)
        else:
            self.__platoonMembers.insert(pos, member)

    def remove_platoon_member(self, member):
        self.__platoonMembers.remove(member)

    def set_to_leader(self):
        self.__isLeader = True

    def is_leader(self):
        return self.__isLeader

    def is_in_platoon(self):
        if self.__platoonLeader is None:
            return False
        return True

    """ ############################################################################
                                Happiness
    ############################################################################ """
    def get_happiness(self, car):
        return self.__get_happiness_table_param(car, 0)

    def get_happiness_counter(self, car):
        return self.__get_happiness_table_param(car, 1)

    def get_happiness_param1(self, car):
        return self.__get_happiness_table_param(car, 2)

    def get_happiness_param2(self, car):
        return self.__get_happiness_table_param(car, 3)

    def __get_happiness_table_param(self, car, index):
        if car in self.__happiness_table:
            return self.__happiness_table[car][index]
        return 0

    def get_happiness_table(self):
        return self.__happiness_table

    def update_happiness(self, candidate, new_happiness, param1=0, param2=0):
        """
        happiness_table =
        {
            #KEY  #Happiness     #N                #Param  #Param
            v1 - [happiness(v1), times_chosen(v1), param1, param2]
            v4 - [happiness(v4), times_chosen(v4), param1, param2]
                .
                .
                .
            v6 - [happiness(v6), times_chosen(v6), param1, param2]
        }
        """
        if candidate in self.__happiness_table:
            times_chosen = self.__happiness_table[candidate][1]
            self.__happiness_table[candidate] = [new_happiness, times_chosen + 1, param1, param2]
            self.__cache.remove(candidate)
            self.__cache.insert(0, candidate)

        else:
            self.__happiness_table[candidate] = [new_happiness, 1, param1, param2]
            self.__cache.insert(0, candidate)
            if DEBUG_HAPPINESS:
                print("INSERTED " + candidate + " in cache of vehicle: " + self.__id)
            if len(self.__happiness_table.values()) > HAPPINESS_TABLE_SIZE:
                deleted = self.__cache.pop(-1)
                # Avoids deleting its own leader.
                if deleted == self.get_platoon_leader():
                    self.__cache.insert(0, deleted)
                    deleted = self.__cache.pop(-1)
                self.__happiness_table.pop(deleted)
                if DEBUG_HAPPINESS:
                    print("REMOVED " + deleted + " from cache of vehicle: " + self.__id)
        if DEBUG_HAPPINESS:
            print("Car: + " + candidate + " Happiness Table: " + str(self.__happiness_table.values()) + " LRU Cache: " + self.__cache)

    """ ############################################################################
                                Getter
    ############################################################################ """

    def get_neighbors(self):
        return self.__neighbors

    def get_candidates(self):
        return self.__candidates

    def get_id(self):
        return self.__id

    def get_float_id(self):
        return self.__floatID

    def get_state(self):
        return self.__state

    def get_platoon_leader(self):
        if self.is_in_platoon():
            return self.__platoonLeader
        return self.__id

    def get_desired_platoon_leader(self):
        return self.__desiredPlatoonLeader

    def get_platoon_members(self):
        if len(self.__platoonMembers) == 0:
            return [self.__id]
        return self.__platoonMembers

    def get_pos_in_platoon(self):
        return int(self.__posInPlatoon)

    def get_desired_speed(self):
        return traci.vehicle.getMaxSpeed(self.__id) * self.__desired_speed_factor  #calculating in m/s!

    def get_desired_platoon_speed(self):
        if self.is_in_platoon():
            return self.__desiredPlatoonSpeed
        return self.get_desired_speed()

    def get_speed(self):
        return traci.vehicle.getSpeed(self.__id)

    def get_max_speed(self):
        return traci.vehicle.getMaxSpeed(self.__id)  #calculating in m/s!

    def get_desired_speed_factor(self):
        return self.__desired_speed_factor

    def get_current_speed_factor(self):
        return traci.vehicle.getSpeedFactor(self.__id)

    def get_lane_id(self):
        """
        Returns the ID of the currently used lane of the road.
        """
        return traci.vehicle.getLaneIndex(self.__id)

    def get_color(self):
        return self.__color

    def get_angle(self):
        return traci.vehicle.getAngle(self.__id)

    def get_road_id(self):
        return traci.vehicle.getRoadID(self.__id)

    def get_neighbor_table_pos(self):
        return self.__neighbor_table_pos

    """ ############################################################################
                                Setter
    ############################################################################ """

    def set_neighbors(self, neighbors):
        self.__neighbors = list(neighbors)

    def set_candidates(self, candidates):
        self.__candidates = list(candidates)

    def set_state(self, state):
        self.__state = state

    def set_platoon_leader(self, leader):
        self.__platoonLeader = leader

    def set_pos_in_platoon(self, pos):
        self.__posInPlatoon = pos

    def set_desired_platoon_speed(self, speed):
        self.__desiredPlatoonSpeed = speed

    def set_current_speed_factor(self, speed_factor):
        traci.vehicle.setSpeedFactor(self.__id, speed_factor)

    def set_neighbor_table_pos(self, pos_relative):
        self.__neighbor_table_pos = pos_relative

    def set_desired_platoon_leader(self, leader):
        self.__desiredPlatoonLeader = leader

    """ ############################################################################
                                Other
    ############################################################################ """

    def colorize(self):
        # print(self.__id)
        if self.__isLeader:
            # print("COLOR --> Own Leader")
            traci.vehicle.setColor(self.__id, self.__color)
        elif self.__platoonLeader is not None:
            # print("COLOR --> Platoon Leader")
            traci.vehicle.setColor(self.__id, traci.vehicle.getColor(self.__platoonLeader))
        else:
            traci.vehicle.setColor(self.__id, STANDARD_COLOR)
            # print("COLOR --> STANDART")


    def on_same_lane_with_leader(self):
        if self.__platoonLeader is None:
            if self.__desiredPlatoonLeader is not None:
                if traci.vehicle.getLaneIndex(self.__id) == traci.vehicle.getLaneIndex(self.__desiredPlatoonLeader) \
                        and traci.vehicle.getAngle(self.__id) == traci.vehicle.getAngle(self.__desiredPlatoonLeader):
                    return True
        else:
            if traci.vehicle.getLaneIndex(self.__id) == traci.vehicle.getLaneIndex(self.__platoonLeader) \
                    and traci.vehicle.getAngle(self.__id) == traci.vehicle.getAngle(self.__platoonLeader):
                return True
        return False

    def left_line_blocked(self):
        neighbors_left_front = traci.vehicle.getNeighbors(self.__id, 0b110)
        neighbors_left_follower = traci.vehicle.getNeighbors(self.__id, 0b100)
        # Bit 0 - 0 left, 1 right
        # Bit 1 - 0 following, 1 leading
        # Bit 2 - 0 all cars, 1 blocking cars
        return len(neighbors_left_follower + neighbors_left_front) > 0

    def right_line_blocked(self):
        neighbors_right_front = traci.vehicle.getNeighbors(self.__id, 0b111)
        neighbors_right_follower = traci.vehicle.getNeighbors(self.__id, 0b101)
        # Bit 0 - 0 left, 1 right
        # Bit 1 - 0 following, 1 leading
        # Bit 2 - 0 all cars, 1 blocking cars
        return len(neighbors_right_follower + neighbors_right_front) > 0

    def reset_car(self):
        self.__isLeader = False
        self.__platoonLeader = None
        self.__platoonMembers = []
        self.__desiredPlatoonSpeed = -1
        self.__posInPlatoon = None
        self.__hasJoiner = False
        self.__hasLeaver = False
        self.colorize()
