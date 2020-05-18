import sys
import os
import random
import math

from VehicleData import VehicleData

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
import CONSTANTS
from plexe import Plexe, DRIVER

# noinspection PyGlobalUndefined
def registry(vehicle_infos_original):
    global vehicleInfos
    vehicleInfos = vehicle_infos_original

def add_vehicles(plexe, n, position, car_counter, real_engine=False):
    """
    Adds a platoon of n vehicles to the simulation, plus an additional one
    farther away that wants to joining_process the platoon
    :param plexe: API instance
    :param n: number of vehicles of the platoon
    :param position: position of the leader
    :param real_engine: set to true to use the realistic engine model,
    false to use a first order lag model
    """
    leader = None
    # add a platoon of n vehicles
    for i in range(n):
        vid = "v.%d" % (i + car_counter)
        if leader is None:
            leader = vid
        #add_platooning_vehicle(plexe, vid,
        #                       position - i * (CONSTANTS.INTER_VERHICLE_DISTANCE + CONSTANTS.VEHICLE_LENGTH),
        #                       0, 25, CONSTANTS.INTER_VERHICLE_DISTANCE, real_engine)
        plexe.set_fixed_lane(vid, 0, safe=False)
        traci.vehicle.setSpeedMode(vid, 0)
        if i == 0:
            plexe.set_active_controller(vid, ACC)
            plexe.enable_auto_lane_changing(leader, True)
        else:
            plexe.set_active_controller(vid, CACC)
            plexe.enable_auto_feed(vid, True, leader, "v.%d" % (i - 1))
            plexe.add_member(leader, vid, i)


def add_vehicle(plexe, car_id, position, lane=-1, speed_in_kmh=-1, vtype=-1, vroute=-1):
    """
    This method adds a car to the simulation. Lane, speed, vtype and vroute are optional.
    If not set, the car is generated randomly.
    In order to generate a non random car, all parameters have to be set.
    """

    if speed_in_kmh is -1:
        # Gaussian distribution with cutoffs. (124, 22) is chosen to imitate a real speed distribution
        # from studies about the german Autobahn.
        speed_in_kmh = random.gauss(124, 22)
    if speed_in_kmh < CONSTANTS.MIN_SPEED_KMH:
        speed_in_kmh = CONSTANTS.MIN_SPEED_KMH
    if speed_in_kmh > CONSTANTS.MAX_SPEED_KMH:
        speed_in_kmh = CONSTANTS.MAX_SPEED_KMH

    # Since 160 km/h (44.44 m/s) is the speed limit, the factor is the speed of
    # the car relative to the maximum speed.
    speed_factor = float(speed_in_kmh) / CONSTANTS.MAX_SPEED_KMH
    speed_in_ms = CONSTANTS.MAX_SPEED_MS * speed_factor

    if vroute is -1:
        vroute = random.randint(0, len(CONSTANTS.ROUTE_TYPES) - 1)

    if lane is -1:
        #Calculates a lane between 0 and 3 related to the driven speed.
        lane = int(math.floor((speed_in_kmh - CONSTANTS.MIN_SPEED_KMH) / (CONSTANTS.MAX_SPEED_KMH - CONSTANTS.MIN_SPEED_KMH) * 3.99))
        if vroute >= 3:
            lane = 0

    traci.vehicle.add(car_id, CONSTANTS.ROUTE_TYPES[vroute], departPos=str(position),
                      departLane=str(lane), departSpeed=speed_in_ms, typeID="passengerGauss")

    plexe.set_active_controller(car_id, DRIVER)
    traci.vehicle.setSpeedMode(car_id, 31)

    vehicleInfos[car_id] = VehicleData(car_id, speed_factor)


