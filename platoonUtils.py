import sys
import os
import math

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
from plexe import DRIVER, ACC, CACC, FAKED_CACC, POS_X, POS_Y, RADAR_DISTANCE
from CONSTANTS import *
import Globals


# noinspection PyGlobalUndefined
def registry(vehicle_infos_original, plexe_original):
    global vehicleInfos
    global plexe
    vehicleInfos = vehicle_infos_original
    plexe = plexe_original


def init_platoon_leader(leader):
    """
    Initializes a car as a platoon leader.
    """

    # Not necessary, but in order to avoid mistakes, the leader information is reset to standard values.
    reset_to_single_car(leader)

    speed = vehicleInfos[leader].get_desired_speed()

    # Updating leader's infomation
    vehicleInfos[leader].set_platoon_leader(leader)
    vehicleInfos[leader].set_state(PLATOON)
    vehicleInfos[leader].set_to_leader()
    vehicleInfos[leader].set_pos_in_platoon(0)
    vehicleInfos[leader].colorize()
    vehicleInfos[leader].add_platoon_member(leader)
    vehicleInfos[leader].set_desired_platoon_speed(speed)
    # Change behaviour into platooning vehicle.
    change_into_platooning_vehicle(leader, speed)
    # Setup lead controller
    plexe.set_active_controller(leader, ACC)
    # Disable lane change. For platoon driving, no member is allowed to change lanes on his own. Instead the leader gets
    # an auto lange change possibility.
    plexe.set_fixed_lane(leader, vehicleInfos[leader].get_lane_id(), False)
    plexe.enable_auto_lane_changing(leader, True)


def add_platoon_member(car, leader):
    """
    Connects a car to an existing platoon leader in order to expand / form a platoon.
    Therefore, the new platoon speed is calculated, the vehicleInfos data stucture is updated,
    the car itself is set up as a platoon vehicle and the leader get an information update.
    Afterwards the car will automatically accelerate and change lanes in order to reach the platoon.
    """
    reset_to_single_car(car)
    nr_of_vehicle_in_platoon = len(vehicleInfos[leader].get_platoon_members())
    # (Derzeitige Durchschnittsgeschwindigkeit * Anzahl derzeitiger Fahrzeuge) + gewuenschte Geschwindigkeit von
    # car, geteilt durch Gesamtmenge an Fahrzeugen.
    speed = ((vehicleInfos[leader].get_desired_platoon_speed() * nr_of_vehicle_in_platoon) + vehicleInfos[
        car].get_desired_speed()) / (nr_of_vehicle_in_platoon + 1)

    # Add information to the data structure.
    vehicleInfos[car].set_platoon_leader(leader)
    vehicleInfos[car].set_pos_in_platoon(nr_of_vehicle_in_platoon)  # Index starts with 0
    vehicleInfos[car].colorize()

    # Set up platooning vehicle
    change_into_platooning_vehicle(car, speed)
    plexe.set_fixed_lane(car, vehicleInfos[leader].get_lane_id(), False)
    plexe.set_active_controller(car, CACC)
    front_car = vehicleInfos[leader].get_platoon_members()[nr_of_vehicle_in_platoon - 1]
    plexe.enable_auto_feed(car, True, leader, front_car)

    # Update leader information
    vehicleInfos[leader].add_platoon_member(car)
    plexe.add_member(leader, car, vehicleInfos[car].get_pos_in_platoon())
    plexe.set_cc_desired_speed(leader, speed)

    for member in vehicleInfos[leader].get_platoon_members():
        vehicleInfos[member].set_desired_platoon_speed(speed)
    
    if DEBUG_ADD_MEMBER:
        print("AddMember Method called")
        print("Car: " + str(car) + " Front car: " + str(front_car) + " Leader: " + str(leader))


def left_lane_blocked(members):
    """
    This method checks, if any of the vehicles inside the members list has a car to its left side.
    If that is the case, the lane is blocked.
    """
    for member in members:
        if vehicleInfos[member].left_line_blocked():
            return True
    return False


def prepare_for_remove(car):
    """
    This is the remove-preprocessing. If the leaving car is the leader itself, it will speed up,
    while the rest of the platoon stays at the current speed.
    If the leaving car is a member, we check the speed of the platoon and the leaver. The faster one will change
    to the left lane. If the car wants to leave the highway soon (and therefore quit the platoon),
    the platoon either changes to the left or if the platoon is not driving on the lane furthest to the right,
    the leaver will change to the lane right.
    """

    leader = vehicleInfos[car].get_platoon_leader()
    vehicleInfos[leader].set_leaver()
    members = list(vehicleInfos[leader].get_platoon_members())
    desired_leader = vehicleInfos[car].get_desired_platoon_leader()
    #Bugfixing method, in case a desired_leader crashes.
    if desired_leader is not None:
        if desired_leader not in vehicleInfos:
            desired_leader = None

    # If all cars want to leave the platoon
    all_vehicles_want_to_leave = True
    for member in members:
        if not (vehicleInfos[member].get_state() == LEFT or vehicleInfos[member].get_state() == LEAVING_PROCESS):
            all_vehicles_want_to_leave = False
    if all_vehicles_want_to_leave:
        for member in members:
            reset_to_single_car(member)
            vehicleInfos[member].set_state(NO_PLATOONING)

    elif vehicleInfos[car].get_lane_id() < 3:
        # CASE 1: Car will join another platoon. Lets compare the laneIDs
        if desired_leader is not None:
            desired_lane = vehicleInfos[vehicleInfos[car].get_desired_platoon_leader()].get_lane_id()
            current_lane = vehicleInfos[car].get_lane_id()

            # only the car will move.
            if current_lane > desired_lane and not vehicleInfos[car].right_line_blocked():
                plexe.set_fixed_lane(car, int(vehicleInfos[leader].get_lane_id() - 1), False)
            # In this situation, the whole platoon will move.
            elif current_lane == desired_lane and not left_lane_blocked(members):
                set_platoon_lane_to(members, int(vehicleInfos[car].get_lane_id() + 1))
            # only the car will move.
            elif current_lane < desired_lane and not vehicleInfos[car].left_line_blocked():
                plexe.set_fixed_lane(car, int(vehicleInfos[leader].get_lane_id() + 1), False)

        # CASE 2: Speed and distance to end check
        # If the platoon is faster than the leaver, the platoon will change lane to the left.
        elif (vehicleInfos[leader].get_desired_platoon_speed() > vehicleInfos[car].get_desired_speed() \
              or plexe.get_distance_to_end(car) - vehicleInfos[car].get_pos_in_platoon() \
              * (INTER_VERHICLE_DISTANCE + VEHICLE_LENGTH) < LEAVE_HIGHWAY_DISTANCE) \
                and not left_lane_blocked(members):
            set_platoon_lane_to(members, int(vehicleInfos[car].get_lane_id() + 1))

        # If the leaver is faster than the platoon, the leaver will change lane to the left.
        elif vehicleInfos[leader].get_desired_platoon_speed() <= vehicleInfos[car].get_desired_speed() \
                and not vehicleInfos[car].left_line_blocked():
            plexe.set_fixed_lane(car, int(vehicleInfos[leader].get_lane_id() + 1), False)

    elif vehicleInfos[car].get_lane_id() >= 3 and not vehicleInfos[car].right_line_blocked():
        plexe.set_fixed_lane(car, int(vehicleInfos[leader].get_lane_id() - 1), False)

    # Identify the new leader (the old one or in case the leader itself will leave, the first member in the platoon)
    leader = get_new_leader(leader, members)

    if vehicleInfos[car].get_lane_id() != vehicleInfos[leader].get_lane_id():
        # After preparing everything for the leaving process, the car will quit the platoon.
        vehicleInfos[car].set_state(LEFT)



def set_platoon_lane_to(members, lane):
    """
    Sets the lane of a platoon. Only affects members in Platoon, Joining or Prepare_Joining state.
    """
    for member in members:
        if vehicleInfos[member].get_state() == PLATOON \
                or vehicleInfos[member].get_state() == JOINING_PROCESS \
                or vehicleInfos[member].get_state() == PREPARE_JOINING:
            plexe.set_fixed_lane(member, lane, False)


def get_new_leader(leader, members):
    """
    Returns the first car in a platoon with state Platoon as the new leader.
    """
    if not vehicleInfos[leader].get_state() == PLATOON:
        for member in members:
            if vehicleInfos[member].get_state() == PLATOON:
                leader = member
                break
    return leader


def remove_platoon_member(car):
    """
    This is the removing process. After the preprocessing (prepare_for_remove) has been called, the car changes into a
    new state, where the remove method is called periodically. First, the removing condition is checked
    (Leader: leaving distance is large enough. Member: the lane is different, and the lane
    changing process is completed.) If the condition is fulfilled, the leaver is removed from all platooning
    information, while the rest platoon is regrouped with the first car as leader.
    """
    leader = vehicleInfos[car].get_platoon_leader()
    vehicleInfos[leader].reset_leaver()
    members = list(vehicleInfos[leader].get_platoon_members())

    #  If platoon size is 2, both cars are reset. If 2 or more cars wants to leave at the same time, it may occur,
    # that the leader itself stays in the platoon. In that case, it has to be reset as well.
    if len(members) <= 2 and car in members:
        for member in members:
            reset_to_single_car(member)
            vehicleInfos[member].set_state(NO_PLATOONING)

    else:
        # Identify the new leader if needed
        if leader == car:
            leader = members[1]
        # leader = get_new_leader(leader_old, members)

        # Setup the new platoon
        # Deleting leader and leaving car information from memberlist.
        if car in members:
            members.remove(car)
        if leader in members:
            members.remove(leader)

        # Initialize the former leader or the former 2. car as the new platoon leader.
        init_platoon_leader(leader)
        # Adds all following cars as platoon members of the new leader. The current state is saved in order to allow
        # other vehicles to leave close to this timestep.
        for member in members:
            if member in vehicleInfos:
                state = vehicleInfos[member].get_state()
                add_platoon_member(member, leader)
                vehicleInfos[member].set_state(state)

        # Delete leaving car platoon information and resets its state.
        reset_to_single_car(car)
        if vehicleInfos[car].get_desired_platoon_leader() is not None:
            vehicleInfos[car].set_state(PREPARE_JOINING)
        else:
            vehicleInfos[car].set_state(NO_PLATOONING)

    if DEBUG_REMOVE_MEMBER:
        print("RemoveMember Method called")
        print("Car: " + str(car) + " DesiredSpeed: " + str(vehicleInfos[car].get_desired_speed())
              + " Leader: " + str(leader) + " DesiredSpeed: " + str(vehicleInfos[leader].get_desired_speed()))


def reset_to_single_car(car):
    """
    Resets a car into a single driving vehicle.
    """
    # Removes all platoon information
    vehicleInfos[car].reset_car()
    # Deactivate auto feed
    plexe.enable_auto_feed(car, False)
    # Deactivate auto lane change
    plexe.enable_auto_lane_changing(car, False)
    # Reset controller to Driver
    plexe.set_active_controller(car, DRIVER)
    # free lane choice
    plexe.disable_fixed_lane(car)


def get_distance(v1, v2):
    """
    Returns the distance between two vehicles, removing the length
    :param v1: id of first vehicle
    :param v2: id of the second vehicle
    :return: distance between v1 and v2
    """
    v1_data = plexe.get_vehicle_data(v1)
    v2_data = plexe.get_vehicle_data(v2)

    distance = math.sqrt((v1_data[POS_X] - v2_data[POS_X]) ** 2 +
                         (v1_data[POS_Y] - v2_data[POS_Y]) ** 2) - 4
    if v1_data[POS_X] > v2_data[POS_X]:
        return - distance
    return distance


def change_into_platooning_vehicle(car, speed):
    plexe.set_path_cacc_parameters(car, INTER_VERHICLE_DISTANCE, 2, 1, 0.5)
    plexe.set_cc_desired_speed(car, speed)
    plexe.set_acc_headway_time(car, 1.5)
    traci.vehicle.setSpeedMode(car, 0)


def merge_platoons(leader_back):
    if vehicleInfos[leader_back].is_leader():
        leader_front = vehicleInfos[leader_back].get_desired_platoon_leader()
        member_back = vehicleInfos[leader_back].get_platoon_members()

        leader_back_lane = vehicleInfos[leader_back].get_lane_id()
        leader_front_lane = vehicleInfos[leader_front].get_lane_id()

        # Road must be the same, else the number of lanes may not fit.
        if vehicleInfos[leader_back].get_road_id() == vehicleInfos[leader_front].get_road_id():

            # leader back is on higher lane than leader front and right lane is not blocked.
            if leader_back_lane > leader_front_lane and vehicleInfos[leader_back].right_line_blocked():
                for member in member_back:
                    plexe.set_fixed_lane(member, vehicleInfos[leader_front].get_lane_id(), False)

            # leader back is on lower lane than leader front and left lane is not blocked.
            elif leader_back_lane < leader_front_lane and vehicleInfos[leader_back].left_line_blocked():
                for member in member_back:
                    plexe.set_fixed_lane(member, vehicleInfos[leader_front].get_lane_id(), False)

            # leader back is on same lane as leader front.
            else:
                vehicleInfos[leader_back].set_desired_platoon_leader(None)
                for member in member_back:
                    add_platoon_member(member, leader_front)
                    vehicleInfos[member].set_state(PLATOON)
                for member in member_back:
                    fix_order(member)


def lane_change(car, leader, neighbors, cautious=False):
    """
    If a car is not on the same lane as its leader, the car tries to switch the lane. This only takes place, if there
    is no other car in between. Else, it will stay on its lane. The cautious variable checks, if the car is aware of
    blocking neighbors or not.
    """
    if not vehicleInfos[car].on_same_lane_with_leader() \
            and vehicleInfos[car].get_road_id() == vehicleInfos[leader].get_road_id() \
            and not cars_in_between(car, vehicleInfos[car].get_platoon_leader(), neighbors):
        plexe.set_fixed_lane(car, vehicleInfos[leader].get_lane_id(), cautious)
    else:
        plexe.set_fixed_lane(car, vehicleInfos[car].get_lane_id(), cautious)


def prepare_joining(car, neighbors):
    """
    This method manages the prepare_joining process.
    The car will change lanes to his leaders lane as soon as possible.
    When joiner and leader are on the same lane and no car is in between, they form up a platoon and the state changes
    to JOINING_PROCESS. At that time auto lane change is disabled.
    """
    leader = vehicleInfos[car].get_desired_platoon_leader()

    lane_change(car, leader, neighbors, True)
    if vehicleInfos[leader].get_current_speed_factor() > vehicleInfos[car].get_current_speed_factor():
        vehicleInfos[car].set_current_speed_factor(vehicleInfos[leader].get_current_speed_factor() * 1.2)

    # Meanwhile, the state of the leader may have changed.
    if (vehicleInfos[leader].get_state() == PLATOON or vehicleInfos[leader].get_state() == SINGLE_CAR) \
            and 0 < get_distance(car, leader) < RADAR_DISTANCE and vehicleInfos[car].get_speed() > 10:
        if vehicleInfos[car].on_same_lane_with_leader() \
                and not cars_in_between(car, leader, neighbors):
            if not vehicleInfos[leader].is_leader():
                init_platoon_leader(leader)
            add_platoon_member(car, leader)
            fix_order(car)
            vehicleInfos[car].set_state(JOINING_PROCESS)
            vehicleInfos[car].set_desired_platoon_leader(None)
            vehicleInfos[car].reset_counter()
    else:
        reset_to_single_car(car)
        vehicleInfos[car].set_desired_platoon_leader(None)
        vehicleInfos[car].set_state(NO_PLATOONING)


def joining_process(car):
    """
    This method surveils the joining process, when a car is on the same lane as the leader and there is no car
    in between. When the car is in platooning distance, auto lane change is enabled again and the car's mode
    changes into Platoon state.
    """
    leader = vehicleInfos[car].get_platoon_leader()
    members = vehicleInfos[leader].get_platoon_members()
    pos = vehicleInfos[car].get_pos_in_platoon()
    predecessor = members[pos - 1]

    if not vehicleInfos[car].on_same_lane_with_leader() \
            and vehicleInfos[car].get_road_id() == vehicleInfos[leader].get_road_id():
        plexe.set_fixed_lane(car, vehicleInfos[leader].get_lane_id(), False)

    if get_distance(car, predecessor) < JOINING_CRITICAL_DISTANCE:
        vehicleInfos[vehicleInfos[car].get_platoon_leader()].reset_joiner()
        vehicleInfos[car].set_state(PLATOON)


def fix_order(car):
    """
    During platoon joining process it may can occur, that a car overtakes its predecessor.
    When the lane of joiner and platoon is the same, this method checks if the platoon is organized in the right order.
    If not, it is reorganized.
    """
    leader = vehicleInfos[car].get_platoon_leader()
    members = vehicleInfos[leader].get_platoon_members()
    pos_car = vehicleInfos[car].get_pos_in_platoon()
    switched = False

    for i in range(len(members)-1):
        predecessor = members[pos_car - 1]
        pos_predecessor = vehicleInfos[predecessor].get_pos_in_platoon()

        if get_distance(car, predecessor) <= - VEHICLE_LENGTH:
            members[pos_car], members[pos_predecessor] = members[pos_predecessor], members[pos_car]
            pos_car = pos_predecessor
            switched = True

            if DEBUG_ADD_MEMBER:
                print("switched " + car + " with " + predecessor)

    if switched:
        leader = members[0]
        members.remove(leader)
        init_platoon_leader(leader)
        for member in members:
            add_platoon_member(member, leader)
            vehicleInfos[member].set_state(PLATOON)

        if DEBUG_ADD_MEMBER:
            print("Fix Order: " + str(vehicleInfos[leader].get_platoon_members()))


def cars_in_between(car, leader_front, neighbors):
    """
    This method checks, if there is a car or platoon in between a car and its platoon it wants to joining_process.
    @param car: The car
    @param leader_front: The new leader of car
    @param neighbors: all neighbors wo are in range and in state Platoon or Single Car
    """
    length_platoon = max(len(vehicleInfos[leader_front].get_platoon_members()), 1) * (
            VEHICLE_LENGTH + INTER_VERHICLE_DISTANCE)
    for neighbor in neighbors:
        # There is a neighbor between the car and its leader
        if -10 < get_distance(car, neighbor) < get_distance(car, leader_front) - length_platoon:
            # This neighbor is not a member of the same platoon as the car or the front leader.
            if not (vehicleInfos[neighbor].get_platoon_leader() == leader_front \
                    or vehicleInfos[neighbor].get_platoon_leader() == vehicleInfos[car].get_platoon_leader()):
                # The neighbor is on the same lane
                if vehicleInfos[neighbor].get_lane_id() == vehicleInfos[leader_front].get_lane_id():
                    return True
                # Or the neighbor is on the lane between car and leader.
                if vehicleInfos[leader_front].get_lane_id() >= vehicleInfos[neighbor].get_lane_id() > vehicleInfos[car].get_lane_id():
                    return True
                if vehicleInfos[leader_front].get_lane_id() <= vehicleInfos[neighbor].get_lane_id() < vehicleInfos[car].get_lane_id():
                    return True
    return False


def calc_ratio(val1, val2):
    """
    This method calculates the ratio between to values. It is always beween 0 and 1.
    """
    if val1 > val2:
        return val2 / val1
    else:
        return val1 / val2


def take_next_exit(car):
    """
    Checks, if the car is near its exit, it wants to take.
    """
    if vehicleInfos[car].is_in_platoon():
        return plexe.get_distance_to_end(car) - vehicleInfos[car].get_pos_in_platoon() \
            * (INTER_VERHICLE_DISTANCE + VEHICLE_LENGTH) < LEAVE_HIGHWAY_DISTANCE
    return plexe.get_distance_to_end(car) < LEAVE_HIGHWAY_DISTANCE


def fix_speed_factor(car):
    if not vehicleInfos[car].get_desired_speed_factor() == vehicleInfos[car].get_current_speed_factor():
        vehicleInfos[car].set_current_speed_factor(vehicleInfos[car].get_desired_speed_factor())


def check_merging(car, neighbor, neighbors):
    """
    Checks conditions, if the platoon of the car may merge his best neighbor.
    """
    if vehicleInfos[car].is_leader() and not vehicleInfos[car].has_joiner() \
            and neighbor is not None:

        if vehicleInfos[neighbor].get_state() is PLATOON:
            leader_front = neighbor
            last_member_front = vehicleInfos[leader_front].get_platoon_members()[-1]
            members_back = vehicleInfos[car].get_platoon_members()
            last_member_back = members_back[-1]

            lane_difference = abs(vehicleInfos[car].get_lane_id() - vehicleInfos[leader_front].get_lane_id())
            # if distance between leader and last_member of front platoon is big enough.
            if get_distance(car, last_member_front) \
                    > (lane_difference + 1) * JOINING_MINIMAL_DISTANCE:
                # if the merged platoon is <= the max allowed amount of vehicles in a platoon.
                if len(vehicleInfos[leader_front].get_platoon_members()) \
                        + len(vehicleInfos[car].get_platoon_members()) <= MAX_PLATOON_SIZE:
                    # If there is no other car in between the last member of the back
                    # platoon and the leader of the front platoon.
                    if not cars_in_between(last_member_back, leader_front, neighbors):
                        vehicleInfos[car].set_desired_platoon_leader(leader_front)
                        for member in members_back:
                            vehicleInfos[member].set_state(MERGING)

                        return True
    return False


def handle_auto_lane_change_in_platoon(car):
    """
    Error routine to make it easier for a car to close up to the platoon.
    While the last platoon member is not on the same lane as the platoon leader, the platoon leader is not allowed to
    do a lange changing maneuver.
    """
    members = vehicleInfos[car].get_platoon_members()
    last_member = members[-1]
    if vehicleInfos[last_member].get_road_id() == vehicleInfos[car].get_road_id() \
            and not vehicleInfos[car].has_leaver() and not vehicleInfos[car].has_joiner():
        plexe.enable_auto_lane_changing(car, True)
    else:
        plexe.enable_auto_lane_changing(car, False)


def check_emergency_platoon_quit(car, leader):
    """
    Error routine to avoid crashes.
    Checks if a car in a platoon is on the wrong lane.
    If the car is overtaking its predecessor, it will quit the platoon immediately.
    If the platoon has no leaver, all cars should stay on the same lane. If it is not the case despite leaving maneuvers,
    the car will move into the right order back.
    """
    if get_distance(car, leader) < VEHICLE_LENGTH:
        if DEBUG_REMOVE_MEMBER:
            print(car + ": emegency platoon quit from leader: " + leader)
        vehicleInfos[car].set_state(LEAVING_PROCESS)
    else:
        plexe.set_fixed_lane(car, vehicleInfos[leader].get_lane_id(), False)


def handle_platoon_changing(car, neighbor, neighbors):
    if neighbor is not None:

        if not cars_in_between(car, neighbor, neighbors) \
                and len(vehicleInfos[neighbor].get_platoon_members()) < MAX_PLATOON_SIZE \
                and not Globals.mode == HEINOVSKI\
                and 0 < get_distance(car, neighbor) < RADAR_DISTANCE:
            if DEBUG_PLATOON_SWITCH:
                print(car + ": " + str(vehicleInfos[car].get_happiness_table())
                      + " : Leader " + vehicleInfos[car].get_platoon_leader()
                      + " : Happiness " + str(vehicleInfos[car].get_happiness(neighbor))
                      + " : Better Leader " + neighbor
                      + " : Better Platoon found.")
            vehicleInfos[car].set_state(LEAVING_PROCESS)
            vehicleInfos[car].set_desired_platoon_leader(neighbor)
            return True
    return False
