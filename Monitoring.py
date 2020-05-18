import csv
from datetime import datetime
import os
from math import floor

import Globals
from CONSTANTS import *
import PlatooningAlgorithms

buffer_size = 100

desired_platoon_speed = [[-1 for i in xrange(AMOUNT_RANDOM_CARS + 1)] for i in xrange(buffer_size)]
desired_speed = [[-1 for i in xrange(AMOUNT_RANDOM_CARS + 1)] for i in xrange(buffer_size)]
speed = [[-1 for i in xrange(AMOUNT_RANDOM_CARS + 1)] for i in xrange(buffer_size)]
speed_factor = [[-1 for i in xrange(AMOUNT_RANDOM_CARS + 1)] for i in xrange(buffer_size)]
platoon_size = [[-1 for i in xrange(AMOUNT_RANDOM_CARS + 1)] for i in xrange(buffer_size)]

happiness = [[-1 for i in xrange(AMOUNT_RANDOM_CARS + 1)] for i in xrange(buffer_size)]
speed_happiness = [[-1 for i in xrange(AMOUNT_RANDOM_CARS + 1)] for i in xrange(buffer_size)]
platoon_size_happiness = [[-1 for i in xrange(AMOUNT_RANDOM_CARS + 1)] for i in xrange(buffer_size)]
distance_to_end_happiness = [[-1 for i in xrange(AMOUNT_RANDOM_CARS + 1)] for i in xrange(buffer_size)]
distance_in_between_happiness = [[-1 for i in xrange(AMOUNT_RANDOM_CARS + 1)] for i in xrange(buffer_size)]

happiness_table = [[-1 for i in xrange(2 * HAPPINESS_TABLE_SIZE + 2)] for i in xrange(buffer_size)]

neighborhood = [[-1 for i in xrange(AMOUNT_RANDOM_CARS + 1)] for i in xrange(buffer_size)]
candidatehood = [[-1 for i in xrange(AMOUNT_RANDOM_CARS + 1)] for i in xrange(buffer_size)]
states = [[-1 for i in xrange(AMOUNT_RANDOM_CARS + 1)] for i in xrange(buffer_size)]

directory = ''

# noinspection PyGlobalUndefined
def registry(vehicle_infos_original):
    global vehicleInfos
    global directory
    vehicleInfos = vehicle_infos_original

    if Globals.mode == E_GREEDY:
        mode = '/__e_greedy'
    elif Globals.mode == UCB1:
        mode = '/__ucb1'
    elif Globals.mode == BAYES_UCB:
        mode = '/__bayes_ucb'
    elif Globals.mode == THOMPSON_SAMPLING:
        mode = '/__thompson_sampling'
    elif Globals.mode == HEINOVSKI:
        mode = '/__heinovski'

    directory = 'data/' + str(Globals.seed) + mode
    if not os.path.exists(directory):
        os.makedirs(directory)
    print("Path now is: " + directory)

    writeHeader(directory + '/desired_platoon_speed.csv')
    writeHeader(directory + '/desired_speed.csv')
    writeHeader(directory + '/speed.csv')
    writeHeader(directory + '/speed_factor.csv')
    writeHeader(directory + '/platoon_size.csv')
    writeHeader(directory + '/happiness.csv')
    writeHeader(directory + '/speed_happiness.csv')
    writeHeader(directory + '/platoon_size_happiness.csv')
    writeHeader(directory + '/distance_to_end_happiness.csv')
    writeHeader(directory + '/distance_in_between_happiness.csv')
    writeHeader(directory + '/happiness_table.csv', nocars=True)
    writeHeader(directory + '/neighborhood.csv')
    writeHeader(directory + '/candidatehood.csv')
    writeHeader(directory + '/states.csv')


def writeHeader(filename, nocars=False):
    with open(filename, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(["NEW SESSION"])
        if nocars:
            writer.writerow([str(datetime.now())])
        else:
            writer.writerow([str(datetime.now())] + range(0, AMOUNT_RANDOM_CARS))



def writeToCSV(array, filename):
    with open(filename, 'a') as f:
        writer = csv.writer(f)
        for i in range(0, buffer_size):
            writer.writerow(array[:][i])


def observe(steps):
    time = (steps / 50) % buffer_size
    #Writes the current timestep into the buffer
    desired_platoon_speed[time][0] = float(steps) / 100
    desired_speed[time][0] = float(steps) / 100
    speed[time][0] = float(steps) / 100
    speed_factor[time][0] = float(steps) / 100
    platoon_size[time][0] = float(steps) / 100
    happiness[time][0] = float(steps) / 100
    speed_happiness[time][0] = float(steps) / 100
    platoon_size_happiness[time][0] = float(steps) / 100
    distance_to_end_happiness[time][0] = float(steps) / 100
    distance_in_between_happiness[time][0] = float(steps) / 100
    happiness_table[time][0] = float(steps) / 100
    neighborhood[time][0] = float(steps) / 100
    candidatehood[time][0] = float(steps) / 100
    states[time][0] = float(steps) / 100

    for car_id in range(0, AMOUNT_RANDOM_CARS):  # type: int
        vehicle = "v." + str(car_id)
        if vehicle in vehicleInfos:

            """ ############################################################################
                                                Speed
            ############################################################################ """
            desired_platoon_speed[time][car_id + 1] = round(vehicleInfos[vehicle].get_desired_platoon_speed(), 2)
            desired_speed[time][car_id + 1] = round(vehicleInfos[vehicle].get_desired_speed(), 2)

            speed_factor[time][car_id + 1] = round(vehicleInfos[vehicle].get_current_speed_factor(), 2)

            speed_value = round(vehicleInfos[vehicle].get_speed(), 2)
            if speed_value < 0:
                speed_value = round(vehicleInfos[vehicle].get_desired_speed(), 2)
            speed[time][car_id + 1] = speed_value

            """ ############################################################################
                                                Platoon Size
            ############################################################################ """
            if vehicleInfos[vehicle].is_in_platoon():
                if vehicleInfos[vehicle].is_leader():
                    platoon_size[time][car_id + 1] = len(vehicleInfos[vehicle].get_platoon_members())
                else:
                    platoon_size[time][car_id + 1] = vehicleInfos[vehicleInfos[vehicle].get_platoon_leader()].get_float_id()
            else:
                platoon_size[time][car_id + 1] = 1

            """ ############################################################################
                                                HAPPINESS
            ############################################################################ """
            happy_value, speed_happiness_value, platoon_size_happiness_value, \
                distance_to_end_happiness_value, distance_in_between_happiness_value \
                = PlatooningAlgorithms.calc_current_happiness_to_neighbor(vehicle, vehicleInfos[vehicle].get_platoon_leader(), full_print=True)
            # Bugfix. When a car is spawned, there is a intervall with a speed value of less than -100.000.
            if happy_value > 1 or happy_value < 0:
                happy_value = 1
            happiness[time][car_id + 1] = round(happy_value, 2)

            if speed_happiness_value > 1 or speed_happiness_value < 0:
                speed_happiness_value = 1
            speed_happiness[time][car_id + 1] = round(speed_happiness_value, 2)

            if platoon_size_happiness_value > 1 or platoon_size_happiness_value < 0:
                platoon_size_happiness_value = 1
            platoon_size_happiness[time][car_id + 1] = round(platoon_size_happiness_value, 2)

            if distance_to_end_happiness_value > 1 or distance_to_end_happiness_value < 0:
                distance_to_end_happiness_value = 1
            distance_to_end_happiness[time][car_id + 1] = round(distance_to_end_happiness_value, 2)

            if distance_in_between_happiness_value > 1 or distance_in_between_happiness_value < 0:
                distance_in_between_happiness_value = 1
            distance_in_between_happiness[time][car_id + 1] = round(distance_in_between_happiness_value, 2)

            """ ############################################################################
                                                Happiness Table
            ############################################################################ """
            if vehicle == "v.16":
                table = vehicleInfos[vehicle].get_happiness_table()
                happiness_table[time][1] = round(PlatooningAlgorithms.calc_current_happiness_to_neighbor(vehicle, vehicle), 2)

                cnt = 2
                for neighbor in table:
                    if not "LRU" in neighbor:
                        happiness_table[time][cnt] = str(neighbor)
                        cnt += 1
                        happiness_table[time][cnt] = str(round(vehicleInfos[vehicle].get_happiness(neighbor), 2) - happiness_table[time][1])
                        cnt += 1
                while cnt < len(happiness_table[time]):
                    happiness_table[time][cnt] = ""
                    cnt += 1

            """ ############################################################################
                                        Neighbor and Candidate hood
            ############################################################################ """
            state = vehicleInfos[vehicle].get_state()
            if state == SINGLE_CAR or (state == PLATOON and not Globals.mode == HEINOVSKI):
                neighborhood[time][car_id + 1] = len(vehicleInfos[vehicle].get_neighbors())
                candidatehood[time][car_id + 1] = len(vehicleInfos[vehicle].get_candidates())
            else:
                neighborhood[time][car_id + 1] = -2
                candidatehood[time][car_id + 1] = -2

            """ ############################################################################
                                        States
            ############################################################################ """
            states[time][car_id + 1] = state

        else:
            desired_platoon_speed[time][car_id + 1] = -1
            desired_speed[time][car_id + 1] = -1
            speed[time][car_id + 1] = -1
            speed_factor[time][car_id + 1] = -1
            platoon_size[time][car_id + 1] = -1
            happiness[time][car_id + 1] = -1
            speed_happiness[time][car_id + 1] = -1
            platoon_size_happiness[time][car_id + 1] = -1
            distance_to_end_happiness[time][car_id + 1] = -1
            distance_in_between_happiness[time][car_id + 1] = -1
            neighborhood[time][car_id + 1] = -1
            candidatehood[time][car_id + 1] = -1
            states[time][car_id + 1] = - 1

    if time == buffer_size - 1:
        writeToCSV(desired_platoon_speed, directory + '/desired_platoon_speed.csv')
        writeToCSV(desired_speed, directory + '/desired_speed.csv')
        writeToCSV(speed, directory + '/speed.csv')
        writeToCSV(speed_factor, directory + '/speed_factor.csv')
        writeToCSV(platoon_size, directory + '/platoon_size.csv')
        writeToCSV(happiness, directory + '/happiness.csv')
        writeToCSV(speed_happiness, directory + '/speed_happiness.csv')
        writeToCSV(platoon_size_happiness, directory + '/platoon_size_happiness.csv')
        writeToCSV(distance_to_end_happiness, directory + '/distance_to_end_happiness.csv')
        writeToCSV(distance_in_between_happiness, directory + '/distance_in_between_happiness.csv')
        writeToCSV(happiness_table, directory + '/happiness_table.csv')
        writeToCSV(neighborhood, directory + '/neighborhood.csv')
        writeToCSV(candidatehood, directory + '/candidatehood.csv')
        writeToCSV(states, directory + '/states.csv')


def write_info(counter, step):
    with open(directory + '/setup.txt', 'a') as f:
        f.write('SEED : ' + str(Globals.seed) + '\n'
                'CARS : ' + str(AMOUNT_RANDOM_CARS) + '\n'
                'RADAR_DISTANCE : ' + str(RADAR_DISTANCE) + '\n'
                'MAX_PLATOON_SIZE : ' + str(MAX_PLATOON_SIZE) + '\n'
                'HAPPINESS_TABLE_SIZE : ' + str(HAPPINESS_TABLE_SIZE) + '\n'
                '----------------------------------------------------------\n'
                'TIME STEPS (in seconds) : ' + str(step / 100) + '\n'
                'CRASHED CARS : ' + str(counter[CRASH]) + '\n'
                'DIRECT PLATOON CHANGES : ' + str(counter[CHANGE]) + '\n'
                'ABORTED CHANGES FROM ABOVE : ' + str(counter[CHANGE_ABORT]) + '\n'
                'MERGED PLATOONS : ' + str(counter[MERGE]) + '\n'
                'ABORTED MERGE FROM ABOVE: ' + str(counter[MERGE_ABORT]) + '\n'                                                
                'END ------------------------------------------------------\n')


def writeGlossary(glossary):
    with open('data/glossary.txt', 'a') as f:
        for entry in glossary:
            if entry[1] == 0:
                f.write('--------------------------------------\n')
            f.write('SEED: ' + str(entry[0]) + ' Mode: ' + str(entry[1]) + ' Step: ' + str(floor(entry[2] / 100)) + '\n')


def write_happiness_change(happiness_change_monitor, suffix):
    with open(directory + '/happiness_change_monitor_' + suffix + '.csv', 'a') as f:
        writer = csv.writer(f)
        for entry in happiness_change_monitor:
            writer.writerow([entry[0], entry[1], round((float(entry[2])/100), 1)])
