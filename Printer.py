import os
from math import floor

import numpy as np
import csv
import matplotlib.pyplot as plt

from CONSTANTS import SINGLE_CAR, JOINING_PROCESS, PREPARE_JOINING, PLATOON, MERGING, LEAVING_PROCESS, LEFT, \
    NO_PLATOONING, NEW_SPAWNED, AMOUNT_RANDOM_CARS

BOXPLOTS = True
ALG_COMPARISON_PLOTS = True
ALG_DETAILED_PLOTS = True
HISTOGRAM = True
COLORS = ['tab:blue', 'tab:orange', 'tab:brown', 'tab:purple', 'tab:cyan', 'tab:olive', 'tab:pink', 'tab:red']
PLOTNAMES = {
    "__bayes_ucb": "Bayes UCB",
    "__ucb1": "UCB 1",
    "__thompson_sampling": "Thompson Sampling",
    "__heinovski": "Heinovski",
    "__e_greedy": "E - Greedy"
}


SMALL_SIZE = 11
MEDIUM_SIZE = 12
BIGGER_SIZE = 16
MEGA_SIZE = 20


def main():
    plt.rc('font', size=MEDIUM_SIZE)  # controls default text sizes
    plt.rc('axes', titlesize=MEGA_SIZE)  # fontsize of the axes title
    plt.rc('axes', labelsize=MEGA_SIZE)  # fontsize of the x and y labels
    plt.rc('xtick', labelsize=BIGGER_SIZE)  # fontsize of the tick labels
    plt.rc('ytick', labelsize=BIGGER_SIZE)  # fontsize of the tick labels
    plt.rc('legend', fontsize=BIGGER_SIZE)  # legend fontsize
    plt.rc('figure', titlesize=MEGA_SIZE)  # fontsize of the figure title

    folder = "data"
    subfolders = os.listdir(folder)
    if BOXPLOTS:
        alg_boxplot(folder)
        print("Boxplots processing")
    statistics(folder)
    if HISTOGRAM:
        histogram(folder)

    for subfolder in subfolders:
        if not (subfolder.endswith(".png") or subfolder.endswith(".txt")):
            subsubfolders = os.listdir(folder + "/" + subfolder)

            if ALG_COMPARISON_PLOTS:
                print("Processing Algorithm Comparison Plots in: " + folder + "/" + subfolder)
                alg_avg_overview(folder + "/" + subfolder)

            if ALG_DETAILED_PLOTS:
                for subsubfolder in subsubfolders:
                    if not subsubfolder.endswith(".png"):
                        path = folder + "/" + subfolder + "/" + subsubfolder
                        print("Detailed Plots in Path: " + path)

                        average_platoon_size(path)
                        desired_current_speed(path)
                        happiness_overview(path)
                        neighbourhood(path)
                        single_car_happiness_change_rate(path)
                        states(path)


def statistics(path):
    tmp_subfolders = os.listdir(path)
    subfolders = []
    # Seeds
    for s in tmp_subfolders:
        if not (s.endswith(".png") or s.endswith(".txt")):
            subfolders.append(s)

    # Algorithm folder names
    tmp_algorithms = os.listdir(path + "/" + subfolders[0])
    algorithms = []
    for a in tmp_algorithms:
        if not (a.endswith(".png") or a.endswith(".txt")):
            algorithms.append(a)

    mean_time = [0 for a in xrange(len(algorithms))]
    mean_crashes = [0 for a in xrange(len(algorithms))]
    mean_changes = [0 for a in xrange(len(algorithms))]
    mean_changes_abort = [0 for a in xrange(len(algorithms))]
    mean_merges = [0 for a in xrange(len(algorithms))]
    mean_merges_abort = [0 for a in xrange(len(algorithms))]

    error_time = [0 for a in xrange(len(algorithms))]
    error_crashes = [0 for a in xrange(len(algorithms))]
    error_changes = [0 for a in xrange(len(algorithms))]
    error_changes_abort = [0 for a in xrange(len(algorithms))]
    error_merges = [0 for a in xrange(len(algorithms))]
    error_merges_abort = [0 for a in xrange(len(algorithms))]

    # For each algorithm
    for a in range(len(algorithms)):

        amount_of_seeds = len(subfolders)
        times = np.zeros(len(subfolders))
        crashes = np.zeros(len(subfolders))
        changes = np.zeros(len(subfolders))
        changes_abort = np.zeros(len(subfolders))
        merges = np.zeros(len(subfolders))
        merges_abort = np.zeros(len(subfolders))

        # Look at each seed
        cnt = 0
        for subfolder in subfolders:
            full_path = path + "/" + subfolder + "/" + algorithms[a]
            f = open(full_path + "/setup.txt", "r")
            for line in f:
                if "TIME STEPS" in line:
                    line = line.lstrip("TIME STEPS (in seconds) : ")
                    times[cnt] = float(line)
                elif "CRASHED CARS" in line:
                    line = line.lstrip("CRASHED CARS : ")
                    crashes[cnt] = float(line)
                elif "PLATOON CHANGES" in line:
                    line = line.lstrip("DIRECT PLATOON CHANGES : ")
                    changes[cnt] = float(line)
                elif "ABORTED CHANGES" in line:
                    line = line.lstrip("ABORTED CHANGES FROM ABOVE : ")
                    changes_abort[cnt] = float(line)
                elif "MERGED PLATOONS" in line:
                    line = line.lstrip("MERGED PLATOONS : ")
                    merges[cnt] = float(line)
                elif "ABORTED MERGE" in line:
                    line = line.lstrip("ABORTED MERGE FROM ABOVE: ")
                    merges_abort[cnt] = float(line)
            cnt += 1

        f.close()

        mean_time[a] = np.mean(times) #0
        mean_crashes[a] = np.mean(crashes) #1
        mean_changes[a] = np.mean(changes) #2
        mean_changes_abort[a] = np.mean(changes_abort) #3
        mean_merges[a] = np.mean(merges) #4
        mean_merges_abort[a] = np.mean(merges_abort) #5

        error_time[a] = np.std(times) #0
        error_crashes[a] = np.std(crashes) #1
        error_changes[a] = np.std(changes) #2
        error_changes_abort[a] = np.std(changes_abort) #3
        error_merges[a] = np.std(merges) #4
        error_merges_abort[a] = np.std(merges_abort) #5


    labels = [None] * len(algorithms)
    for a in range(len(algorithms)):
        labels[a] = PLOTNAMES[algorithms[a]]

    fig, ax = plt.subplots()
    fig.set_size_inches(14.5, 9.5)
    plt.title("Average Simulation Time (n = " + str(amount_of_seeds) + ")")
    ax.set_ylabel('Time in seconds')

    x = np.arange(len(algorithms))
    rect = ax.bar(x, mean_time, yerr=error_time, align='center', alpha=0.5, ecolor='gray', capsize=10)
    autolabel(rect, ax)
    plt.xticks(x, labels)
    ax.yaxis.grid(True)
    ax.set_ylim((0, 700))
    fig.savefig(path + "/AVG_Simulation_Time.png")
    plt.close()


    fig, ax = plt.subplots()
    fig.set_size_inches(14.5, 9.5)
    ax.set_ylabel('Average Amount')
    ax.set_title("Average Occurrences (n = " + str(amount_of_seeds) + ")")
    ax.set_xticks(x)
    ax.set_xticklabels(['Crashes', 'Changes', 'Changes Aborted', 'Merges', 'Merges Aborted'])
    ax.set_ylim((0, 200))

    width = 0.16
    start_offset = -0.32
    cnt = 0

    for a in range(len(algorithms)):
        array_mean = mean_crashes[a], mean_changes[a], mean_changes_abort[a], mean_merges[a], mean_merges_abort[a]
        array_error = error_crashes[a], error_changes[a], error_changes_abort[a], error_merges[a], error_merges_abort[a]
        rect = ax.bar(x + (start_offset + cnt * width), array_mean, width, yerr=array_error, align='center', alpha=0.5, ecolor='gray', capsize=10, label=PLOTNAMES[algorithms[a]], color=COLORS[cnt])
        autolabel(rect, ax)

        cnt += 1

    ax.yaxis.grid(True)
    ax.legend()
    fig.savefig(path + "/AVG_Occurences.png")
    plt.close()


def autolabel(rects, ax):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = round(rect.get_height(),1)
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')


def histogram(path):
    tmp_subfolders = os.listdir(path)
    subfolders = []
    # Seeds
    for s in tmp_subfolders:
        if not (s.endswith(".png") or s.endswith(".txt")):
            subfolders.append(s)

    # Algorithm folder names
    tmp_algorithms = os.listdir(path + "/" + subfolders[0])
    algorithms = []
    for a in tmp_algorithms:
        if not (a.endswith(".png") or a.endswith(".txt")):
            algorithms.append(a)


    single_car_data = [[] for a in xrange(len(algorithms))]
    platoon_data = [[] for a in xrange(len(algorithms))]
    labels_single_car = [[] for a in xrange(len(algorithms))]
    labels_platoon = [[] for a in xrange(len(algorithms))]
    to_be_removed_line = 0

    # For each algorithm
    for a in range(len(algorithms)):
        if algorithms[a] != '__heinovski':
            happiness_changes_single_car = None
            happiness_changes_platoon = None

            for subfolder in subfolders:
                full_path = path + "/" + subfolder + "/" + algorithms[a]

                happiness_changes_single_car = extract_and_concatenate(full_path + "/happiness_change_monitor_vehicle.csv", happiness_changes_single_car)
                happiness_changes_platoon = extract_and_concatenate(full_path + "/happiness_change_monitor_platoon.csv", happiness_changes_platoon)

            difference = len(happiness_changes_single_car) - len(happiness_changes_platoon)
            happiness_changes_platoon = np.concatenate([happiness_changes_platoon, np.zeros(difference)])

            single_car_data[a] = happiness_changes_single_car
            platoon_data[a] = happiness_changes_platoon
            labels_single_car[a] = PLOTNAMES[algorithms[a]] + ": " + str(round(np.sum(happiness_changes_single_car) / len(happiness_changes_single_car), 2))
            labels_platoon[a] = PLOTNAMES[algorithms[a]] + ": " + str(round(np.sum(happiness_changes_platoon) / len(happiness_changes_platoon), 2))

        else:
            to_be_removed_line = a

    single_car_data = np.delete(single_car_data, to_be_removed_line, 0)
    platoon_data = np.delete(platoon_data, to_be_removed_line, 0)

    fig, ax = plt.subplots(2, 1)
    fig.set_size_inches(14.5, 10.5)
    plt.suptitle("Happiness Improvement Histogram")
    ax[0].set_xlabel("Happiness Improvement of a Single Car")
    ax[1].set_xlabel("Happiness Improvement of the Platoon")
    ax[0].set_ylabel("Frequency")
    ax[1].set_ylabel("Frequency")
    ax[0].hist(single_car_data, bins=33, range=(-0.4, 0.7), density=False, histtype='bar', label=labels_single_car, color=COLORS[0:4])
    ax[1].hist(platoon_data, bins=33, range=(-0.4, 0.7), density=False, histtype='bar', label=labels_platoon, color=COLORS[0:4])
    ax[0].set_xticks(np.arange(-0.4, 0.75, 0.1))
    ax[1].set_xticks(np.arange(-0.4, 0.75, 0.1))
    ax[0].legend()
    ax[1].legend()
    fig.savefig(path + "/Histogramm_Platoon_Changes.png")
    plt.close()




def extract_and_concatenate(path, happiness_changes):
    with open(path, 'r') as f:
        array = list(csv.reader(f, delimiter=","))
        array = np.array(array)  # , dtype=np.float
        if len(array) > 0:
            vehicle_changes = array[:, 1]
            vehicle_changes = np.array(vehicle_changes, dtype=np.float)
            if happiness_changes is None:
                happiness_changes = vehicle_changes
            else:
                happiness_changes = np.concatenate([happiness_changes, vehicle_changes])
    return happiness_changes


def colorize_bps(bp, threshold=1000):

    ## change outline color, fill color and linewidth of the boxes
    cnt = 0
    for box in bp['boxes']:
        # change outer color
        box.set(color=COLORS[cnt], linewidth=2)
        cnt = (cnt + 1) % threshold

    ## change color and linewidth of the whiskers
    cnt = 0
    for whisker in bp['whiskers']:
        whisker.set(color=COLORS[int(floor(cnt))], linewidth=2)
        cnt = (cnt + 0.5) % threshold

    ## change color and linewidth of the caps
    cnt = 0
    for cap in bp['caps']:
        cap.set(color=COLORS[int(floor(cnt))], linewidth=2)
        cnt = (cnt + 0.5) % threshold

    ## change color and linewidth of the medians
    for median in bp['medians']:
        median.set(color='#3A4145', linewidth=2)


def make_boxplot(path, x_tick1, x_tick2, platoon_size_data, xlabel, ylabel, title, ylim, colorize=False, legend=None, amount_of_bars=1000):
    fig, ax = plt.subplots()
    fig.set_size_inches(14.5, 10.5)
    plt.title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_ylim(ylim)
    bp = ax.boxplot(platoon_size_data)
    if colorize:
        legend = list(legend)
        for i in range(len(legend)):
            legend[i] = PLOTNAMES[legend[i]]
        colorize_bps(bp, threshold=amount_of_bars)
        ax.legend([bp["boxes"][0], bp["boxes"][1], bp["boxes"][2], bp["boxes"][3], bp["boxes"][4]], legend,
                  loc="lower right")

    plt.xticks(x_tick1, x_tick2)
    fig.savefig(path + "/" + title + ".png")
    plt.close()


def alg_boxplot(path):
    tmp_subfolders = os.listdir(path)
    subfolders = []
    for s in tmp_subfolders:
        if not (s.endswith(".png") or s.endswith(".txt")):
            subfolders.append(s)

    tmp_algorithms = os.listdir(path + "/" + subfolders[0])
    algorithms = []
    for a in tmp_algorithms:
        if not (a.endswith(".png") or a.endswith(".txt")):
            algorithms.append(a)

    timesteps = np.arange(50, 600, 50)
    #       Aufrufreihenfolge data[algorithm][timestep]
    average_platoon_size = [[[] for i in xrange(len(timesteps))] for a in xrange(len(algorithms))]
    average_happiness = [[[] for i in xrange(len(timesteps))] for a in xrange(len(algorithms))]

    for a in range(len(algorithms)):
        for subfolder in subfolders:
            full_path = path + "/" + subfolder + "/" + algorithms[a]

            platoon_size = csv_to_array(full_path + "/platoon_size.csv")
            happiness = csv_to_array(full_path + "/happiness.csv")

            cnt = 0
            for step in timesteps:
                # for every line in array
                if len(platoon_size) / 2 > step:
                    platoon_size_step = (platoon_size[step, 1:])
                    happiness_step = (happiness[step, 1:])
                    # amount of cars is actually the same
                    amount_of_cars = np.sum((platoon_size_step > -1))

                    platoon_leaders = np.sum((platoon_size_step > -1) & (platoon_size_step < 1000))
                    average_platoon_size[a][cnt].append(float(amount_of_cars) / platoon_leaders)

                    happiness_sum = sum(happiness_step) - amount_of_cars + len(happiness_step)
                    average_happiness[a][cnt].append(float(happiness_sum) / amount_of_cars)
                cnt += 1

    # One plot for each algorithm.
    # for all algorithms
    for a in range(len(algorithms)):
        platoon_size_data = []
        happiness_data = []
        n = []

        # append all timestep - lists to one list for boxplotting
        for timestep in range(len(timesteps)):
            platoon_size_data.append(average_platoon_size[a][timestep])
            happiness_data.append(average_happiness[a][timestep])
            n.append(len(average_platoon_size[a][timestep]))

        x_ticks1 = np.arange(1, len(timesteps) + 1)
        x_ticks2 = []

        for i in range(len(timesteps)):
            timestep = str(timesteps[i]) + " (n=" + str(n[i]) + ")"
            x_ticks2.append(timestep)

        make_boxplot(path, x_ticks1, x_ticks2, platoon_size_data, 'Time samples (s)', 'Average Platoon Size',
                     "Average Platoon Size Boxplot - " + PLOTNAMES[algorithms[a]], (0.75, 3.25))
        make_boxplot(path, x_ticks1, x_ticks2, happiness_data, 'Time samples (s)', 'Average Happiness',
                     "Average Happiness Boxplot - " + PLOTNAMES[algorithms[a]], (0.5, 0.8))

    # One big single plot
    platoon_size_data = []
    happiness_data = []
    # for all algorithms
    for timestep in range(len(timesteps)):

        # append all timestep - lists to one list for boxplotting
        for a in range(len(algorithms)):
            platoon_size_data.append(average_platoon_size[a][timestep])
            happiness_data.append(average_happiness[a][timestep])
        # Gap between two time steps.
        platoon_size_data.append([])
        platoon_size_data.append([])
        happiness_data.append([])
        happiness_data.append([])

    # +2 because of gap between time steps.
    x_tick1 = np.arange(3, len(timesteps) * (len(algorithms)+2) + 1, 7)
    x_tick2 = timesteps
    make_boxplot(path, x_tick1, x_tick2, platoon_size_data, 'Time samples (s)',
                 "Average Platoon Size", "Average Platoon Size Boxplot (n = " + str(len(subfolders)) + ")", (0.75, 3.25), colorize=True,
                 legend=algorithms,  amount_of_bars=7)
    make_boxplot(path, x_tick1, x_tick2, happiness_data, 'Time samples (s)',
                 'Average Happiness', "Average Happiness Boxplot (n = " + str(len(subfolders)) + ")", (0.5, 0.9), colorize=True,
                 legend=algorithms,  amount_of_bars=7)


def alg_avg_overview(path):
    subsubfolders = os.listdir(path)

    # Plotting
    fig1, ax1 = plt.subplots()
    fig1.set_size_inches(14.5, 10.5)
    plt.title("Platoon Size")
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Average Platoon Size')
    ax1.set_ylim((1, 3.2))

    fig2, ax2 = plt.subplots()
    fig2.set_size_inches(14.5, 10.5)
    plt.title("Happiness")
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Average Happiness')
    ax2.set_ylim((0.5, 0.8))
    # ----------------------------------------------------- #

    cnt = 0

    for subsubfolder in subsubfolders:
        if not subsubfolder.endswith(".png"):
            platoon_size = csv_to_array(path + "/" + subsubfolder + "/platoon_size.csv")
            happiness = csv_to_array(path + "/" + subsubfolder + "/happiness.csv")

            time = (platoon_size[:, 0])
            average_platoon_size = np.zeros(len(time))
            average_happiness = np.zeros(len(time))
            cut_off_cnt = 0

            for i in range(len(time)):
                # for every line in array
                platoon_size_step = (platoon_size[i, 1:])
                happiness_step = (happiness[i, 1:])

                # amount of cars is actually the same
                amount_of_cars = np.sum((platoon_size_step > -1))

                # division zero.
                if amount_of_cars > 0:
                    platoon_leaders = np.sum((platoon_size_step > -1) & (platoon_size_step < 1000))
                    average_platoon_size[i] = float(amount_of_cars) / platoon_leaders

                    happiness_sum = sum(happiness_step) - amount_of_cars + len(happiness_step)
                    average_happiness[i] = float(happiness_sum) / amount_of_cars
                else:
                    cut_off_cnt += 1

            color = COLORS[cnt]
            label = PLOTNAMES[subsubfolder]
            cnt += 1

            ax1.plot(time[cut_off_cnt:], average_platoon_size[cut_off_cnt:], color=color, label=label)
            ax2.plot(time[cut_off_cnt:], average_happiness[cut_off_cnt:], color=color, label=label)

    ax1.legend(loc="lower right")
    ax2.legend(loc="lower right")
    fig1.tight_layout()  # otherwise the right y-label is slightly clipped
    fig2.tight_layout()  # otherwise the right y-label is slightly clipped
    fig1.savefig(path + "/AVG_Platoon_Size.png")
    fig2.savefig(path + "/AVG_Happiness.png")
    plt.close()


def single_car_happiness_change_rate(path):
    happiness = csv_to_array(path + "/happiness.csv")

    time = (happiness[:, 0])
    cars = [10, 20, 30, 40]

    car_happiness = np.zeros((len(cars), len(time)))

    for i in range(len(time)):
        # for every line in array
        happiness_step = (happiness[i, 1:])

        for j in range(len(cars)):
            car_happiness[j, i] = happiness_step[cars[j]]

    # Plotting
    fig, ax1 = plt.subplots()
    fig.set_size_inches(14.5, 10.5)

    plt.title("Single Car Happiness")
    ax1.set_xlabel('time (s)')
    ax1.set_ylabel('happiness')
    plt.ylim(0, 1)

    for i in range(len(cars)):
        color = COLORS[i]
        ax1.plot(time, car_happiness[i, :], color=color, label="car " + str(cars[i]))
    ax1.legend(loc="upper right")

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.savefig(path + "/Happiness Change Rate Single Car.png")
    plt.close()


def csv_to_array(path):
    with open(path, 'r') as f:
        array = list(csv.reader(f, delimiter=","))
        return np.array(array[2:], dtype=np.float)


def happiness_overview(path):
    happiness = csv_to_array(path + "/happiness.csv")
    speed_happiness = csv_to_array(path + "/speed_happiness.csv")
    platoon_size_happiness = csv_to_array(path + "/platoon_size_happiness.csv")
    distance_to_end_happiness = csv_to_array(path + "/distance_to_end_happiness.csv")
    distance_in_between_happiness = csv_to_array(path + "/distance_in_between_happiness.csv")

    time = (happiness[:, 0])

    average_happiness = np.zeros(len(time))
    average_speed_happiness = np.zeros(len(time))
    average_platoon_size_happiness = np.zeros(len(time))
    average_distance_to_end_happiness = np.zeros(len(time))
    average_distance_in_between_happiness = np.zeros(len(time))

    cut_off_cnt = 0

    for i in range(len(time)):
        # for every line in array
        happiness_step = (happiness[i, 1:])
        speed_happiness_step = (speed_happiness[i, 1:])
        platoon_size_happiness_step = (platoon_size_happiness[i, 1:])
        distance_to_end_happiness_step = (distance_to_end_happiness[i, 1:])
        distance_in_between_happiness_step = (distance_in_between_happiness[i, 1:])

        # amount of cars is actually the same
        amount_of_cars = np.sum((happiness_step > -1))

        # division zero.
        if amount_of_cars > 0:
            happiness_sum = sum(happiness_step) + (len(happiness_step) - amount_of_cars)
            average_happiness[i] = (float(happiness_sum) / amount_of_cars)

            speed_happiness_sum = sum(speed_happiness_step) + (len(happiness_step) - amount_of_cars)
            average_speed_happiness[i] = (float(speed_happiness_sum) / amount_of_cars)

            platoon_size_happiness_sum = sum(platoon_size_happiness_step) + (len(happiness_step) - amount_of_cars)
            average_platoon_size_happiness[i] = (float(platoon_size_happiness_sum) / amount_of_cars)

            distance_to_end_happiness_sum = sum(distance_to_end_happiness_step) + (len(happiness_step) - amount_of_cars)
            average_distance_to_end_happiness[i] = (float(distance_to_end_happiness_sum) / amount_of_cars)

            distance_in_between_happiness_sum = sum(distance_in_between_happiness_step) + (
                    len(happiness_step) - amount_of_cars)
            average_distance_in_between_happiness[i] = (float(distance_in_between_happiness_sum) / amount_of_cars)
        else:
            cut_off_cnt += 1

    x_data = time[cut_off_cnt:]
    y_data = average_happiness[cut_off_cnt:], average_speed_happiness[cut_off_cnt:], \
             average_platoon_size_happiness[cut_off_cnt:], average_distance_to_end_happiness[cut_off_cnt:], \
             average_distance_in_between_happiness[cut_off_cnt:]
    data_labels = "Overall", "Speed Happiness", "Platoon Size", "Distance To End", "Distance In Between"
    make_plot(path, x_data, y_data, 'Time (s)', 'Average Happiness', "Happiness Overview", data_labels=data_labels)


def states(path):
    state_list = csv_to_array(path + "/states.csv")

    time = (state_list[:, 0])
    single_car_cnt = np.zeros(len(time))
    join_cnt = np.zeros(len(time))
    platoon_cnt = np.zeros(len(time))
    leave_cnt = np.zeros(len(time))
    no_platoon_cnt = np.zeros(len(time))
    amount_of_cars_cnt = np.zeros(len(time))
    cut_off_cnt = 0

    for i in range(len(time)):
        # for every line in array
        states_step = (state_list[i, 1:])

        # amount of cars is actually the same
        amount_of_cars = np.count_nonzero(states_step != -1)

        # division zero.
        if amount_of_cars > 0:
            single_car_cnt[i] = float(np.count_nonzero(states_step == SINGLE_CAR)) / AMOUNT_RANDOM_CARS
            join_cnt[i] = float(
                np.count_nonzero((states_step == PREPARE_JOINING) | (states_step == JOINING_PROCESS))) / AMOUNT_RANDOM_CARS
            platoon_cnt[i] = float(
                np.count_nonzero((states_step == PLATOON) | (states_step == MERGING))) / AMOUNT_RANDOM_CARS
            leave_cnt[i] = float(
                np.count_nonzero((states_step == LEAVING_PROCESS) | (states_step == LEFT))) / AMOUNT_RANDOM_CARS
            no_platoon_cnt[i] = float(
                np.count_nonzero((states_step == NO_PLATOONING) | (states_step == NEW_SPAWNED))) / AMOUNT_RANDOM_CARS
            amount_of_cars_cnt[i] = float(amount_of_cars) / AMOUNT_RANDOM_CARS
        else:
            cut_off_cnt += 1

    # Plotting
    fig, ax1 = plt.subplots()
    fig.set_size_inches(14.5, 10.5)

    plt.title("States of Vehicles")
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Amount of Vehicles (relative)')

    labels = ["Single Cars", "Joining Cars", "Leaving Cars", "Not Platooning Cars", "Platooning Cars"]
    cnt = [single_car_cnt, join_cnt, leave_cnt, no_platoon_cnt, platoon_cnt]


    for i in range(len(labels)):
        ax1.plot(time, cnt[i], color=COLORS[i], label=labels[i])

    ax1.legend(loc="upper left")
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.savefig(path + "/States_Of_Cars_Relative.png")
    plt.close()


    # Plotting
    fig, ax1 = plt.subplots()
    fig.set_size_inches(14.5, 10.5)

    plt.title("States of Vehicles")
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Amount of Vehicles')

    labels = ["Single Cars", "Joining Cars", "Leaving Cars", "Not Platooning Cars", "Platooning Cars"]

    join_cnt += single_car_cnt
    leave_cnt += join_cnt
    no_platoon_cnt += leave_cnt
    platoon_cnt += no_platoon_cnt

    cnt = [single_car_cnt*250, join_cnt*250, leave_cnt*250, no_platoon_cnt*250, platoon_cnt*250]
    ground = np.zeros(len(single_car_cnt))


    for i in range(len(labels)):
        if i == 4:
            ax1.fill_between(time, cnt[4-i], ground, color=COLORS[4-i], alpha=0.5, label=labels[4-i])
        else:
            ax1.fill_between(time, cnt[4-i], cnt[(4 - i) - 1], color=COLORS[4-i], alpha=0.5, label=labels[4-i])
    ax1.plot(time, platoon_cnt*250, color='tab:gray', label="Amount of Cars")

    ax1.legend(loc="upper left")



    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.savefig(path + "/States_Of_Cars_Absolut.png")
    plt.close()


def neighbourhood(path):
    neighboorhood = csv_to_array(path + "/neighborhood.csv")
    candidatehood = csv_to_array(path + "/candidatehood.csv")

    time = (neighboorhood[:, 0])
    average_neighborhood = np.zeros(len(time))
    average_candidatehood = np.zeros(len(time))
    cut_off_cnt = 0

    for i in range(len(time)):
        # for every line in array
        neighborhood_step = neighboorhood[i, 1:]
        candidatehood_step = candidatehood[i, 1:]

        # amount of cars is actually the same
        amount_of_cars = np.sum((neighborhood_step != -1))
        # counts -2 in candidatehood step. This signals a existing car not in State Platoon or Single_car
        amount_of_cars_in_wrong_state = np.sum((candidatehood_step == -2))
        amount_of_single_and_platoon_cars = amount_of_cars - amount_of_cars_in_wrong_state

        # division zero.
        if amount_of_single_and_platoon_cars > 0:
            neighborhood_sum = sum(neighborhood_step) - amount_of_cars + len(
                neighborhood_step) + 2 * amount_of_cars_in_wrong_state
            candidate_sum = sum(candidatehood_step) - amount_of_cars + len(
                neighborhood_step) + 2 * amount_of_cars_in_wrong_state
            average_neighborhood[i] = float(neighborhood_sum) / amount_of_single_and_platoon_cars
            average_candidatehood[i] = float(candidate_sum) / amount_of_single_and_platoon_cars

        else:
            cut_off_cnt += 1

    x_data = time
    y_data = average_neighborhood, average_candidatehood
    data_labels = "Neighborhood", "Candidatehood"
    make_plot(path, x_data, y_data, 'Time (s)', 'Average Amount', "Neighborhood", data_labels=data_labels)


def make_plot(path, x_data, y_data, xlabel, ylabel, title, data_labels=None):
    # Plotting
    fig, ax = plt.subplots()
    fig.set_size_inches(14.5, 10.5)

    plt.title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    for i in range(len(y_data)):
        color = COLORS[i]
        ax.plot(x_data, y_data[i], color=color, label=data_labels[i])
    if data_labels is not None:
        ax.legend(loc="upper right")

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.savefig(path + "/" + title + ".png")
    plt.close()


def average_platoon_size(path):
    platoon_size = csv_to_array(path + "/platoon_size.csv")
    happiness = csv_to_array(path + "/happiness.csv")

    time = (platoon_size[:, 0])
    average_platoon_size = np.zeros(len(time))
    average_happiness = np.zeros(len(time))

    cut_off_cnt = 0

    for i in range(len(time)):
        # for every line in array
        platoon_size_step = (platoon_size[i, 1:])
        happiness_step = (happiness[i, 1:])

        # amount of cars is actually the same
        amount_of_cars = np.sum((platoon_size_step > -1))

        # division zero.
        if amount_of_cars > 0:
            platoon_leaders = np.sum((platoon_size_step > -1) & (platoon_size_step < 1000))
            average_platoon_size[i] = float(amount_of_cars) / platoon_leaders

            happiness_sum = sum(happiness_step) - amount_of_cars + len(happiness_step)
            average_happiness[i] = float(happiness_sum) / amount_of_cars
        else:
            cut_off_cnt += 1

    # Plotting
    fig, ax1 = plt.subplots()
    fig.set_size_inches(14.5, 10.5)

    plt.title("Platoon Size vs. Happiness")
    color = 'tab:red'
    ax1.set_xlabel('time (s)')
    ax1.set_ylabel('average platoon size', color=color)
    ax1.set_ylim((1, 3))
    ax1.plot(time[cut_off_cnt:], average_platoon_size[cut_off_cnt:], color=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('average happiness', color=color)  # we already handled the x-label with ax1
    ax2.set_ylim((0.5, 0.8))
    ax2.plot(time[cut_off_cnt:], average_happiness[cut_off_cnt:], color=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.savefig(path + "/Platoon Size vs Happiness.png")
    plt.close()


def desired_current_speed(path):
    speed = csv_to_array(path + "/speed.csv")
    desired_speed = csv_to_array(path + "/desired_speed.csv")
    desired_platoon_speed = csv_to_array(path + "/desired_platoon_speed.csv")

    desired_speed_difference = abs(speed - desired_speed)
    desired_platoon_speed_difference = abs(speed - desired_platoon_speed)

    time = (speed[:, 0])
    sum_desired_speed_difference = np.zeros(len(time))
    sum_desired_platoon_speed_difference = np.zeros(len(time))
    amount_of_cars_array = np.zeros(len(time))

    for i in range(len(time)):
        # for every line in array
        desired_speed_difference_step = (desired_speed_difference[i, 1:])
        desired_platoon_speed_difference_step = (desired_platoon_speed_difference[i, 1:])
        speed_step = (speed[i, 1:])

        # amount of cars is actually the same
        amount_of_cars = np.sum((speed_step > -1))

        if amount_of_cars > 0:
            # - amount_of_cars + len(speed_step) removes all -1 in this array.
            sum_speed = sum(speed_step) - amount_of_cars + len(speed_step)
            sum_desired_speed_difference[i] = sum(desired_speed_difference_step) / sum_speed
            sum_desired_platoon_speed_difference[i] = sum(desired_platoon_speed_difference_step) / sum_speed
            amount_of_cars_array[i] = amount_of_cars
        else:
            sum_desired_speed_difference[i] = 0
            sum_desired_platoon_speed_difference[i] = 0
            amount_of_cars_array[i] = 0

    x_data = time
    y_data = sum_desired_speed_difference, sum_desired_platoon_speed_difference
    data_labels = "Desired Speed", "Desired Platoon Speed"
    make_plot(path, x_data, y_data, 'Time (s)', 'Deviation (relative)', "Speed Loss", data_labels=data_labels)

    y_data = [amount_of_cars_array]
    data_labels = ["Cars"]
    make_plot(path, x_data, y_data, 'Time (s)', 'Amount Of Cars', "Amount of Cars", data_labels=data_labels)


if __name__ == "__main__":
    main()
