#Configurable
MAX_PLATOON_SIZE = 8
RADAR_DISTANCE = 150
AMOUNT_RANDOM_CARS = 250

# available types
# 0 - 3
# 4 - 6
# 7 - 8
# 9
ROUTE_TYPES = "start_to_dest_1", "start_to_dest_2", "start_to_dest_3", "start_to_end", \
              "dest_1_to_dest_2", "dest_1_to_dest_3", "dest_1_to_end",\
              "dest_2_to_dest_3", "dest_2_to_end", \
              "dest_3_to_end"
EDGES = "E2", "E6", "E10", "E14"

# PLATOON Variables
VEHICLE_LENGTH = 4
INTER_VERHICLE_DISTANCE = 5
JOINING_MINIMAL_DISTANCE = 12
JOINING_CRITICAL_DISTANCE = 10
LEAVE_HIGHWAY_DISTANCE = 1200
PLATOON_CHANGING_THRESHOLD = 0  # Paramter t in Master's Thesis
DECISION_THRESHOLD = 1          # Paramter w in Master's Thesis
STANDARD_COLOR = 41, 84, 107, 255


# Modes                         # Paramter SCENARIO in Master's Thesis
START_TO_END_SCENARIO = 0
DYNAMIC_SCENARIO = 1
MODE = DYNAMIC_SCENARIO

# COUNTER
CAR = 0
CRASH = 1
CHANGE = 2
MERGE = 3
CHANGE_ABORT = 4
MERGE_ABORT = 5

#STATES
NEW_SPAWNED = 0
SINGLE_CAR = 1
PREPARE_JOINING = 2
JOINING_PROCESS = 3
PLATOON = 4
MERGING = 5
LEAVING_PROCESS = 6
LEFT = 7
NO_PLATOONING = 8

# SPEED
MAX_SPEED_KMH = 160
MIN_SPEED_KMH = 110
MAX_SPEED_MS = round(MAX_SPEED_KMH / 3.6, 2)

# Weighting factors for happiness algorithms. Normalizing is done in happiness routine.
W_DISTANCE_TO_END = 1               # Paramter alpha in Master's Thesis
W_DISTANCE_IN_BETWEEN = 1           # Paramter beta in Master's Thesis
W_SPEED = 2                         # Paramter gamma in Master's Thesis
W_PLATOON_SIZE = 2                  # Paramter delta in Master's Thesis

BASE_SPEED = 1
BASE_DISTANCE_TO_END = 0
BASE_PLATOON_SIZE = 1 / MAX_PLATOON_SIZE


# The amount of relationships stored into a cars database. New entries are managed on LRU basis.
HAPPINESS_TABLE_SIZE = 5

# Mode
E_GREEDY = 0
UCB1 = 1
BAYES_UCB = 2
THOMPSON_SAMPLING = 3
HEINOVSKI = 4

#HAPPINESS MODE
CURRENT = 0
MEAN = 1

#E_GREEDY
E_GREEDY_E = 0.1
#BAYES_UCB
VARIANCE_FACTOR = 2
#THOMPSON SAMPLING
INITIAL_ALPHA = 1
INITIAL_BETA = 1

# DEBUG
DEBUG_PLATOON_MERGING_ALLOWED = True #Standard True
DEBUG_PRINT_PLATOON_DESIRED_REAL_SPEED = False #Standard False
DEBUG_ADD_MEMBER = False #Standart False
DEBUG_REMOVE_MEMBER = False #Standart False
DEBUG_CREATE = False #Standard False
DEBUG_HAPPINESS = False  #Standard False
DEBUG_PLATOON_SWITCH = False