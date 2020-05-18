#!/usr/bin/env python

import os
import sys
import random
import math
from time import sleep

import Monitoring

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
from plexe import Plexe, DRIVER, RADAR_DISTANCE, POS_X

import utils
import createUtils
import platoonUtils
import PlatooningAlgorithms
import Globals
from CONSTANTS import *


def half_second(step):
    return step % 50 == 0


def second(step):
    return step % 100 == 0


def hundred_ms_times(factor, step):
    return step % (factor * 10) == 0


def main():
    seeds = [4,5,6,7,8,9,10, 11]
    modes = [E_GREEDY, UCB1, BAYES_UCB, THOMPSON_SAMPLING, HEINOVSKI]
    glossary = []

    for seed in seeds:
        for mode in modes:

            try:
                Globals.mode = mode
                Globals.seed = seed
                random.seed(seed)
                sleep(0.5)
                utils.start_sumo("cfg/freeway.sumo.cfg", False, gui=True)
                # used to randomly color the vehicles
                plexe = Plexe()
                traci.addStepListener(plexe)
                step = 0
                counter = [0, 0, 0, 0, 0, 0]
                happiness_change_monitor_vehicle = []
                happiness_change_monitor_platoon = []
                spawn_timer = 40
                spawn_threshold = random.randint(200, 300)
                vehicleInfos = {}
                platoonUtils.registry(vehicleInfos, plexe)
                Monitoring.registry(vehicleInfos)
                createUtils.registry(vehicleInfos)
                PlatooningAlgorithms.registry(vehicleInfos, plexe)
                neighbor_table = [[] for i in range(500)]
                spawning_list = []
                spawnable_list = []

                # Reset simulation afer 6 Minutes.
                while step <= 60002:
                    try:
                        traci.simulationStep()
                    except:
                        print(sys.exc_info()[0])
                    """ ############################################################################
                                                Setup Vehicles
                    ############################################################################ """

                    all_vehicles = list(traci.vehicle.getIDList())
                    vehicles = list(all_vehicles)
                    spawn_timer += 1

                    # Generating cars every second (100 timesteps)
                    if spawn_timer >= spawn_threshold and len(vehicles) < AMOUNT_RANDOM_CARS:
                        spawn_timer = 0

                        if len(spawnable_list) == 0:
                            car_id = "v.%d" % counter[CAR]
                            counter[CAR] += 1
                        else:
                            car_id = spawnable_list.pop(0)

                        if len(spawning_list) != 0:
                            spawnable_list.append(spawning_list.pop(0))

                        # 0 - 3     Start
                        # 4 - 6     1. Entry
                        # 7 - 8     2. Entry
                        # 9         3. Entry
                        spawn_threshold = random.randint(200, 300)

                        if step < 17000:
                            vroute = random.randint(0, 3)
                        elif step < 34000:
                            vroute = random.randint(0, 6)
                            spawn_threshold /= 1.5
                        elif step < 51000:
                            vroute = random.randint(0, 8)
                            spawn_threshold /= 2

                        if MODE == START_TO_END_SCENARIO:
                            createUtils.add_vehicle(plexe, car_id, 0, vroute=3)
                        else:
                            createUtils.add_vehicle(plexe, car_id, 0, vroute=vroute)

                    """ ############################################################################
                                                Simulate
                    ############################################################################ """

                    # for every existing car, do the following actions every 100 ms
                    if hundred_ms_times(2, step):

                        """ ############################################################################
                                        Removing Routine at the End of a Car's Route
                        ############################################################################ """

                        for car in all_vehicles:
                            if car in vehicleInfos:

                                if plexe.get_distance_to_end(car) < 10 or plexe.get_crashed(car) or 0 < vehicleInfos[car].get_speed() < 0.5:
                                    if vehicleInfos[car].is_in_platoon():
                                        platoonUtils.remove_platoon_member(car)
                                    pos_relative = int(vehicleInfos[car].get_neighbor_table_pos())
                                    if car in neighbor_table[pos_relative]:
                                        neighbor_table[pos_relative].remove(car)

                                    if plexe.get_crashed(car) or 0 < vehicleInfos[car].get_speed() < 1:
                                        counter[CRASH] += 1
                                        traci.vehicle.remove(car)
                                    spawning_list.append(car)
                                    vehicleInfos.pop(car)

                            if car not in vehicleInfos:
                                vehicles.remove(car)
                        """ ############################################################################
                                                    Update Neighbor Table
                        ############################################################################ """
                        for car in vehicles:
                            pos_relative = int(math.floor(plexe.get_vehicle_data(car)[POS_X] / RADAR_DISTANCE))
                            pos_relative_old = int(vehicleInfos[car].get_neighbor_table_pos())
                            if pos_relative_old is not pos_relative:
                                if car in neighbor_table[pos_relative_old]:
                                    neighbor_table[pos_relative_old].remove(car)
                                neighbor_table[pos_relative].append(car)
                                vehicleInfos[car].set_neighbor_table_pos(pos_relative)

                        """ ############################################################################
                                                    Update Neighbors
                        ############################################################################ """

                        for car in vehicles:
                            state = vehicleInfos[car].get_state()
                            position = vehicleInfos[car].get_neighbor_table_pos()

                            # add all vehicles in the specific neighbor_table area to the neighbors list
                            if position == 0:
                                neighbors = neighbor_table[position] + neighbor_table[position + 1]
                            else:
                                neighbors = neighbor_table[position - 1] + neighbor_table[position] + neighbor_table[position + 1]
                            # The current car is not a neighbor of itself
                            if car in neighbors:
                                neighbors.remove(car)

                            vehicleInfos[car].set_neighbors(neighbors)

                            """ ############################################################################
                                                           Happiness Update and Algorithms
                            ############################################################################ """
                            if (state == SINGLE_CAR or (state == PLATOON and not Globals.mode == HEINOVSKI)) \
                                    and hundred_ms_times(10, step):
                                neighbor = PlatooningAlgorithms.processing_neighbor_search(car, neighbors)
                            else:
                                neighbor = None

                            """ ############################################################################
                                                           Perform State Actions
                               ############################################################################ """

                            """ ############################################################################
                                                           State = NEW_SPAWNED
                               ############################################################################ """
                            if state == NEW_SPAWNED:
                                vehicleInfos[car].set_current_speed_factor(vehicleInfos[car].get_desired_speed_factor())

                                if vehicleInfos[car].get_road_id() in EDGES:
                                    vehicleInfos[car].set_state(SINGLE_CAR)
                                    if DEBUG_CREATE:
                                        print(car + " start speed: " + str(vehicleInfos[car].get_speed())
                                              + " start speed factor: " + str(vehicleInfos[car].get_desired_speed_factor()))
                                        print(car + " switches to Single Car State")

                            elif state == SINGLE_CAR:
                                """ ############################################################################
                                                               State = SINGLE_CAR
                                   ############################################################################ """
                                platoonUtils.fix_speed_factor(car)

                                if platoonUtils.take_next_exit(car):
                                    if DEBUG_REMOVE_MEMBER:
                                        print(car + ": " + str(plexe.get_distance_to_end(car)) + " m distance to end")
                                    vehicleInfos[car].set_state(NO_PLATOONING)

                                elif neighbor is not None and hundred_ms_times(10, step):
                                    if not platoonUtils.cars_in_between(car, neighbor, neighbors) \
                                            and len(vehicleInfos[neighbor].get_platoon_members()) < MAX_PLATOON_SIZE:
                                        last_member = vehicleInfos[neighbor].get_platoon_members()[-1]

                                        lane_difference = abs(
                                            vehicleInfos[car].get_lane_id() - vehicleInfos[neighbor].get_lane_id())
                                        # It is only possible to join a platoon, if car is behind the last member of the
                                        # existing platoon.
                                        if platoonUtils.get_distance(car, last_member) \
                                                > (lane_difference + 1) * JOINING_MINIMAL_DISTANCE:
                                            vehicleInfos[car].set_state(PREPARE_JOINING)
                                            vehicleInfos[car].set_desired_platoon_leader(neighbor)
                                            vehicleInfos[neighbor].set_joiner()

                            elif state == PREPARE_JOINING:
                                """ ############################################################################
                                                               State = PREPARE_JOINING
                                   ############################################################################ """
                                # For monitoring purpose only
                                desired_leader = vehicleInfos[car].get_desired_platoon_leader()
                                members = vehicleInfos[desired_leader].get_platoon_members()
                                member_happiness_list = {}
                                for member in members:
                                    member_happiness_list[member] = PlatooningAlgorithms.calc_new_happiness(member, desired_leader)

                                platoonUtils.prepare_joining(car, neighbors)

                                # For monitoring purpose only
                                if not vehicleInfos[car].get_state() == PREPARE_JOINING and vehicleInfos[car].is_from_another_platoon():
                                    if vehicleInfos[car].get_state() == NO_PLATOONING:
                                        counter[CHANGE_ABORT] += 1

                                    # Monitoring happiness change of single car
                                    leader = vehicleInfos[car].get_platoon_leader()
                                    new_happiness = PlatooningAlgorithms.calc_new_happiness(car, leader)
                                    happiness_difference = vehicleInfos[car].get_old_happiness() - new_happiness
                                    happiness_change_monitor_vehicle.append((car, happiness_difference, step))

                                    # Monitoring happiness change of joined platoon if change was successful.
                                    if leader == desired_leader:
                                        members = vehicleInfos[leader].get_platoon_members()
                                        happiness_difference = 0
                                        for member in members:
                                            if member in member_happiness_list:
                                                new_happiness = PlatooningAlgorithms.calc_new_happiness(member, leader)
                                                happiness_difference += (member_happiness_list[member] - new_happiness)
                                        happiness_change_monitor_platoon.append((leader, happiness_difference, step))
                                    vehicleInfos[car].reset_from_another_platoon()

                            elif state == JOINING_PROCESS:
                                """ ############################################################################
                                                               State = JOINING_PROCESS
                                   ############################################################################ """
                                platoonUtils.joining_process(car)
                                # This routine checks, whether the car wants to leave the highway soon.
                                # If that is the case, the car will leave its platoon.
                                leader = vehicleInfos[car].get_platoon_leader()
                                if platoonUtils.take_next_exit(car) or platoonUtils.cars_in_between(car, leader, neighbors):
                                    if DEBUG_REMOVE_MEMBER:
                                        print(car + ": " + str(plexe.get_distance_to_end(car)) + " m distance to end")
                                    vehicleInfos[car].set_state(LEAVING_PROCESS)

                            elif state == PLATOON:
                                """ ############################################################################
                                                               State = PLATOON
                                   ############################################################################ """
                                # DEBUG: Platoon desired / real speed
                                if DEBUG_PRINT_PLATOON_DESIRED_REAL_SPEED and vehicleInfos[car].is_leader():
                                    print(str(car) + ": DesiredSpeed: " + str(
                                        vehicleInfos[car].get_desired_speed()) + " isSpeed: " + str(vehicleInfos[car].get_speed()))
                                    members = vehicleInfos[car].get_platoon_members()
                                    for member in members[1::]:
                                        print("member: " + str(member) + ": DesiredSpeed: " + str(
                                            vehicleInfos[member].get_desired_speed()) + " isSpeed: " + str(
                                            vehicleInfos[member].get_speed()))
                                    print("----------------------------------------------------------------------")

                                if DEBUG_PLATOON_MERGING_ALLOWED and hundred_ms_times(10, step) \
                                        and Globals.mode != HEINOVSKI:
                                    if platoonUtils.check_merging(car, neighbor, neighbors):
                                        counter[MERGE] += 1

                                if vehicleInfos[car].is_leader():
                                    platoonUtils.handle_auto_lane_change_in_platoon(car)
                                else:  # if not vehicleInfos[car].is_leader()
                                    leader = vehicleInfos[car].get_platoon_leader()
                                    if vehicleInfos[leader].get_state() == PLATOON \
                                            and not vehicleInfos[car].on_same_lane_with_leader() \
                                            and vehicleInfos[car].get_road_id() == vehicleInfos[leader].get_road_id():
                                        # Checks, if a platooned car is on the wrong lane and handles the situation.
                                        platoonUtils.check_emergency_platoon_quit(car, leader)

                                if vehicleInfos[car].get_state() == PLATOON and hundred_ms_times(10, step):
                                    # This routine checks, whether the car wants to leave the highway soon.
                                    if platoonUtils.take_next_exit(car):
                                        if DEBUG_REMOVE_MEMBER:
                                            print(car + ": " + str(plexe.get_distance_to_end(car)) + " m distance to end")
                                        vehicleInfos[car].set_state(LEAVING_PROCESS)

                                    # This routine checks, whether better platoons are available.
                                    if not vehicleInfos[car].has_joiner():
                                        if platoonUtils.handle_platoon_changing(car, neighbor, neighbors):
                                            leader = vehicleInfos[car].get_platoon_leader()
                                            old_happiness = PlatooningAlgorithms.calc_new_happiness(car, leader)

                                            counter[CHANGE] += 1
                                            vehicleInfos[car].set_from_another_platoon()
                                            vehicleInfos[car].set_old_happiness(old_happiness)

                            elif state == MERGING:
                                """ ############################################################################
                                                               State = MERGING
                                   ############################################################################ """
                                if vehicleInfos[car].is_leader():
                                    leader_front = vehicleInfos[car].get_desired_platoon_leader()
                                    members = vehicleInfos[car].get_platoon_members()

                                    # Platoon is out of range, abort.
                                    if platoonUtils.get_distance(car, leader_front) > RADAR_DISTANCE:
                                        counter[MERGE_ABORT] += 1
                                        for member in members:
                                            vehicleInfos[member].set_state(PLATOON)
                                    elif not platoonUtils.cars_in_between(members[-1], leader_front, neighbors):
                                        platoonUtils.merge_platoons(car)

                            elif state == LEAVING_PROCESS:
                                """ ############################################################################
                                                               State = LEAVING_PROCESS
                                   ############################################################################ """
                                platoonUtils.prepare_for_remove(car)

                            elif state == LEFT:
                                """ ############################################################################
                                                               State = LEFT
                                   ############################################################################ """
                                platoonUtils.remove_platoon_member(car)

                            elif state == NO_PLATOONING:
                                """ ############################################################################
                                                                State = NO_PLATOONING
                                ############################################################################ """
                                # Adjust speed factor to desired after leaving a platoon.
                                if platoonUtils.take_next_exit(car) and vehicleInfos[car].get_lane_id() != 0:
                                    vehicleInfos[car].set_current_speed_factor(0.5)
                                else:
                                    platoonUtils.fix_speed_factor(car)

                                if not platoonUtils.take_next_exit(car):
                                    if vehicleInfos[car].get_counter() >= 20:
                                        vehicleInfos[car].set_state(SINGLE_CAR)
                                        if DEBUG_PLATOON_SWITCH:
                                            print(car + " is reset into SINGLE CAR STATE")
                                        vehicleInfos[car].reset_counter()
                                    else:
                                        vehicleInfos[car].inc_counter()

                    """ ############################################################################
                                                Monitoring
                    ############################################################################ """
                    if half_second(step):
                        Monitoring.observe(step)
                    step += 1

            except:
                print(sys.exc_info())
                print("Simulation " + str(seed) + " stops at step " + str(step))

            Monitoring.write_info(counter, step)
            Monitoring.write_happiness_change(happiness_change_monitor_vehicle, "vehicle")
            Monitoring.write_happiness_change(happiness_change_monitor_platoon, "platoon")
            traci.close()
            glossary.append((seed, mode, step))

    Monitoring.writeGlossary(glossary)


if __name__ == "__main__":
    main()
