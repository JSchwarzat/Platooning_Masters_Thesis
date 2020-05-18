import math
import sys
import os
import random

import numpy as np

import Globals
import platoonUtils

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
from CONSTANTS import *


def __calc_happiness(speed1, speed2, platoon_size, car, members, distance_in_between):
    """
    This method calculates the four different happiness values and forms a single happiness related to
    the predefined weighting factors.
    All values are normalized in the intervall [0,1]
    """
    speed_happiness = calc_speed_happiness(speed1, speed2)
    platoon_size_happiness = calc_platoon_size_happiness(platoon_size)
    distance_to_end_happiness = calc_distance_to_end_happiness(car, members)
    distance_in_between_happiness = calc_distance_in_between_happiness(distance_in_between)

    happiness = (W_SPEED * speed_happiness
                 + W_PLATOON_SIZE * platoon_size_happiness
                 + W_DISTANCE_TO_END * distance_to_end_happiness
                 + W_DISTANCE_IN_BETWEEN * distance_in_between_happiness) \
                / (W_SPEED + W_PLATOON_SIZE + W_DISTANCE_TO_END + W_DISTANCE_IN_BETWEEN)
    return happiness, speed_happiness, platoon_size_happiness, distance_to_end_happiness, distance_in_between_happiness


def calc_current_happiness_to_neighbor(car, neighbor, full_print=False):
    """
    Calculates the current happiness of a car to a specific neighbor. If neighbor is the own leader or the car itself,
    the happiness is still calculated.
    """
    desired_speed_car = float(vehicleInfos[car].get_desired_speed())
    is_speed = float(vehicleInfos[neighbor].get_speed())
    members = vehicleInfos[neighbor].get_platoon_members()
    distance_in_between = platoonUtils.get_distance(car, neighbor)

    own_leader = vehicleInfos[car].get_platoon_leader()
    if own_leader == neighbor:
        platoon_size = len(members)
    else:
        platoon_size = len(members) + 1

    if full_print:
        return __calc_happiness(desired_speed_car, is_speed, platoon_size, car, members, distance_in_between)
    return __calc_happiness(desired_speed_car, is_speed, platoon_size, car, members, distance_in_between)[0]


def calc_speed_happiness(speed_self, speed_neighbor):
    speed_self = float(max(speed_self - 19, 0.1))
    speed_neighbor = float(max(speed_neighbor - 19, 0.1))
    return min(speed_self / speed_neighbor, speed_neighbor / speed_self)


def calc_platoon_size_happiness(size):
    return float(1 - (float(1) / size))


def calc_distance_to_end_happiness(car, members):
    distance_to_end_car = plexe.get_distance_to_end(car)
    distance_to_end_neighbor = 0
    for member in members:
        if member != car:
            distance_to_end_neighbor = max(plexe.get_distance_to_end(member), distance_to_end_neighbor)
            if distance_to_end_car <= distance_to_end_neighbor:
                break
    if distance_to_end_neighbor == 0:
        return 0
    else:
        return min(1, (float(distance_to_end_car) / distance_to_end_neighbor))


def calc_distance_in_between_happiness(distance):
    return max(1 - (float(distance) / RADAR_DISTANCE), 0)


def calc_new_happiness(car, best_neighbor):
    """
    This method gets the current happiness value and returns either the value or the calculated mean, dependant
    on the happiness_mode.
    """
    happiness_value = calc_current_happiness_to_neighbor(car, best_neighbor)
    if Globals.happiness_mode == CURRENT:
        return happiness_value
    elif Globals.happiness_mode == MEAN:
        times_chosen = vehicleInfos[car].get_happiness_counter(best_neighbor)
        mean = (happiness_value + times_chosen * vehicleInfos[car].get_happiness(best_neighbor)) / (
                times_chosen + 1)
        return mean
    return 0


def __e_greedy(car, candidates):
    happiness = vehicleInfos[car].get_happiness_table()
    best_value = 0
    best_neighbor = None

    if len(candidates) > 0:
        e = random.random()
        if e < E_GREEDY_E:
            best_neighbor = candidates[random.randint(0, len(candidates) - 1)]

        else:
            for candidate in candidates:
                # If no entry exists, a new entry is opened
                # suggestion time.
                if candidate not in happiness:
                    new_happiness = calc_current_happiness_to_neighbor(car, candidate)
                    vehicleInfos[car].update_happiness(candidate, new_happiness, new_happiness)

                # GREEDY APPROACH
                # looking for the match with highest value stored in the table.
                mean = vehicleInfos[car].get_happiness_param1(candidate)
                if mean >= best_value:
                    best_value = mean
                    best_neighbor = candidate

        # Update the best fitting candidate with current happiness.
        new_happiness = calc_new_happiness(car, best_neighbor)
        times_chosen = vehicleInfos[car].get_happiness_counter(best_neighbor)

        mean = (new_happiness + times_chosen * vehicleInfos[car].get_happiness(best_neighbor)) / (times_chosen + 1)

        # Store the happiness inside the car.
        vehicleInfos[car].update_happiness(best_neighbor, new_happiness, mean)


def __ucb1(car, candidates):
    happiness = vehicleInfos[car].get_happiness_table()
    best_value = 0
    best_neighbor = None
    amount_of_tries = 0

    if len(candidates) > 0:
        for candidate in candidates:
            # If no entry exists, a new entry is opened
            # suggestion time.
            if candidate not in happiness:
                new_happiness = calc_current_happiness_to_neighbor(car, candidate)
                vehicleInfos[car].update_happiness(candidate, new_happiness)

            amount_of_tries += vehicleInfos[car].get_happiness_counter(candidate)

        for candidate in candidates:
            # GREEDY APPROACH
            # looking for the match with highest value stored in the table.
            happiness_value = vehicleInfos[car].get_happiness(candidate)
            # calculating confidence on basis of amount_of_tries (overall) and counter of each car.
            heuristic_value = math.sqrt((2 * math.log(amount_of_tries + 1, 10))
                                        / (vehicleInfos[car].get_happiness_counter(candidate) + 1))

            if happiness_value + heuristic_value >= best_value:
                best_value = happiness_value + heuristic_value
                best_neighbor = candidate

        # Update the best fitting candidate with current happiness.
        new_happiness = calc_new_happiness(car, best_neighbor)
        # Store the happiness inside the car.
        vehicleInfos[car].update_happiness(best_neighbor, new_happiness)


def __bayes_ucb(car, candidates):
    happiness = vehicleInfos[car].get_happiness_table()
    best_value = 0
    best_neighbor = None

    if len(candidates) > 0:
        for candidate in candidates:
            # If no entry exists, a new entry is opened
            # suggestion time.
            if candidate not in happiness:
                new_happiness = calc_current_happiness_to_neighbor(car, candidate)
                vehicleInfos[car].update_happiness(candidate, new_happiness, 0)

            # BAYES UCB
            # looking for the match with highest value stored in the table.
            mean = vehicleInfos[car].get_happiness(candidate)
            variance = vehicleInfos[car].get_happiness_param1(candidate)

            if mean + VARIANCE_FACTOR * math.sqrt(variance) >= best_value:
                best_value = mean + VARIANCE_FACTOR * math.sqrt(variance)
                best_neighbor = candidate

        # Update the best fitting candidate with current happiness.

        # Is only used to store value into table.
        happiness_value = calc_new_happiness(car, best_neighbor)
        # Is used for calculations of the algorithm.
        curr_happiness = calc_current_happiness_to_neighbor(car, best_neighbor)
        # Modifying best happiness related to the algorithm.
        times_chosen = vehicleInfos[car].get_happiness_counter(best_neighbor)
        old_mean = vehicleInfos[car].get_happiness_param1(best_neighbor)
        new_mean = (curr_happiness + times_chosen * old_mean) / (
                times_chosen + 1)
        old_variance = vehicleInfos[car].get_happiness_param2(best_neighbor)
        new_variance = old_variance + ((curr_happiness - old_mean) * (curr_happiness - new_mean) - old_variance) / (times_chosen + 1)

        # Store the happiness inside the car.
        vehicleInfos[car].update_happiness(best_neighbor, happiness_value, new_mean, new_variance)


def __thompson_sampling(car, candidates):
    happiness = vehicleInfos[car].get_happiness_table()
    best_value = 0
    best_neighbor = None

    if len(candidates) > 0:
        for candidate in candidates:
            # If no entry exists, a new entry is opened
            # suggestion time.
            if candidate not in happiness:
                new_happiness = calc_current_happiness_to_neighbor(car, candidate)
                vehicleInfos[car].update_happiness(candidate, new_happiness, INITIAL_ALPHA, INITIAL_BETA)

            # looking for the match with highest value stored in the table.
            alpha = vehicleInfos[car].get_happiness_param1(candidate)
            beta = vehicleInfos[car].get_happiness_param2(candidate)
            sample = np.random.beta(alpha, beta)

            if sample >= best_value:
                best_value = sample
                best_neighbor = candidate

        # Update the best fitting candidate with current happiness.
        # Is only used to store value into table.
        happiness_value = calc_new_happiness(car, best_neighbor)
        # Is used for calculations of the algorithm.
        curr_happiness = calc_current_happiness_to_neighbor(car, best_neighbor)
        # Modifying best happiness related to the algorithm.
        old_alpha = vehicleInfos[car].get_happiness_param1(best_neighbor)
        new_alpha = old_alpha + curr_happiness
        old_beta = vehicleInfos[car].get_happiness_param2(best_neighbor)
        new_beta = old_beta + (1 - curr_happiness)

        # Store the happiness inside the car.
        vehicleInfos[car].update_happiness(best_neighbor, happiness_value, new_alpha, new_beta)


def __heinovski(car, candidates):
    desired_speed_car = float(vehicleInfos[car].get_desired_speed())

    best_car = ""
    f = 1000

    for candidate in candidates:
        state = vehicleInfos[candidate].get_state()
        if state == SINGLE_CAR or state == PLATOON:
            speed_deviation = abs(desired_speed_car - float(vehicleInfos[candidate].get_speed()))
            distance = platoonUtils.get_distance(car, candidate)
            if distance < 0:
                distance = 9999

            f_new = 0.6 * speed_deviation * 3.6 + 0.4 * distance

            if f_new < f:
                f = f_new
                best_car = candidate

    table = list(vehicleInfos[car].get_happiness_table())
    for vehicle in table:
        vehicleInfos[car].get_happiness_table().pop(vehicle)
    if best_car != "":
        vehicleInfos[car].update_happiness(best_car, 1)


def update_happiness_table(car, neighbors):
    """
    This method decides, which happiness shall be updated.
    @neighbors: a list with all detected vehicles in range, who are single or platoon leader.
    """
    if Globals.mode == E_GREEDY:
        __e_greedy(car, neighbors)
    elif Globals.mode == UCB1:
        __ucb1(car, neighbors)
    elif Globals.mode == BAYES_UCB:
        __bayes_ucb(car, neighbors)
    elif Globals.mode == THOMPSON_SAMPLING:
        __thompson_sampling(car, neighbors)
    elif Globals.mode == HEINOVSKI:
        __heinovski(car, neighbors)


def choose_best_neighbor(car, candidates):
    """
    This method iterates over all candidates and looks them up in the happiness table of the car. If the candidate with
    the highest value fits the choosing conditions, it is returned. Else None is returned.
    ***
        CHOOSING CONDITIONS
        - either a car was choosen at least max(10, amount_of_candidates * 3) times
            or amount of tries over all cars is > amount_of_candidates * 10
        - best neighbor value is above HAPPY_THRESHOLD_MIN
        - distance between car and best neighbor is between 0 and RADAR_DISTANCE
    """
    if len(candidates) > 0:
        best_value = 0
        best_neighbor = None
        happiness = vehicleInfos[car].get_happiness_table()

        amount_of_tries = 0

        for candidate in candidates:
            if candidate in happiness:
                amount_of_tries += vehicleInfos[car].get_happiness_counter(candidate)

                if vehicleInfos[car].get_happiness(candidate) > best_value:
                    best_value = vehicleInfos[car].get_happiness(candidate)
                    best_neighbor = candidate

        if best_neighbor is not None:
            # if platoon leader, no change is required.
            if best_neighbor == vehicleInfos[car].get_platoon_leader():
                return None
            # Routine for all algorithms except heinovski
            if Globals.mode is not HEINOVSKI:
                # Threshold for avoiding platoon changes cause of minimal benefit
                if vehicleInfos[car].is_in_platoon():
                    happiness_value = calc_new_happiness(car, vehicleInfos[car].get_platoon_leader())
                    if happiness_value + PLATOON_CHANGING_THRESHOLD > best_value:
                        return None
                # If best neighbor is in radar distance and exploring has ended.
                if vehicleInfos[car].get_happiness_counter(best_neighbor) >= max(DECISION_THRESHOLD, math.floor(len(candidates) * 2.5)) \
                        or vehicleInfos[car].get_state() == SINGLE_CAR:
                    if 0 < platoonUtils.get_distance(car, best_neighbor) < RADAR_DISTANCE:
                        return best_neighbor
            # Heinovski special routine.
            elif 0 < platoonUtils.get_distance(car, best_neighbor) < RADAR_DISTANCE:
                return best_neighbor
    return None


# noinspection PyGlobalUndefined
def registry(vehicle_infos_original, plexe_original):
    global vehicleInfos
    global plexe
    vehicleInfos = vehicle_infos_original
    plexe = plexe_original


def filter_neighbors(car, neighbors):
    """
    This method returns neighbors, who are in a fitting state and fitting distance.
    Returned neighbors are always a SINGLE CAR or a PLATOON LEADER. If a PLATOON MEMBER is detected, its LEADER
    is added.
    """
    own_leader = vehicleInfos[car].get_platoon_leader()
    candidates = []
    for neighbor in neighbors:
        if 0 < platoonUtils.get_distance(car, neighbor) < RADAR_DISTANCE:
            if vehicleInfos[neighbor].get_state() == PLATOON:
                leader = vehicleInfos[neighbor].get_platoon_leader()
                if leader not in candidates:
                    candidates.append(leader)
            elif vehicleInfos[neighbor].get_state() == SINGLE_CAR:
                candidates.append(neighbor)
    if own_leader is not None:
        if own_leader not in candidates:
            candidates.append(own_leader)
    return candidates


def processing_neighbor_search(car, neighbors):
    candidates = filter_neighbors(car, neighbors)
    vehicleInfos[car].set_candidates(candidates)
    update_happiness_table(car, candidates)
    return choose_best_neighbor(car, candidates)
