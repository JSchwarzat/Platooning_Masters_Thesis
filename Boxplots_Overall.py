import os
from math import floor

import numpy as np
import csv
import matplotlib.pyplot as plt

from CONSTANTS import SINGLE_CAR, JOINING_PROCESS, PREPARE_JOINING, PLATOON, MERGING, LEAVING_PROCESS, LEFT, \
    NO_PLATOONING, NEW_SPAWNED, AMOUNT_RANDOM_CARS


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


def csv_to_array(path):
    with open(path, 'r') as f:
        array = list(csv.reader(f, delimiter=","))
        return np.array(array[2:], dtype=np.float)


def boxplots(path):

    tmp_scenarios = os.listdir(path)
    scenarios = []
    for scenario in tmp_scenarios:
        if not (scenario.endswith(".png") or scenario.endswith(".txt")):
            scenarios.append(path + "/" + scenario)

    # One big single plot
    platoon_size_data = []
    happiness_data = []
    labels = []


    for scenario in sorted(scenarios):
        tmp_seeds = os.listdir(scenario)
        seeds = []
        for s in tmp_seeds:
            if not (s.endswith(".png") or s.endswith(".txt")):
                seeds.append(s)

        tmp_algorithms = os.listdir(scenario + "/" + seeds[0])
        algorithms = []
        for a in tmp_algorithms:
            if not (a.endswith(".png") or a.endswith(".txt")):
                algorithms.append(a)

        timesteps = np.arange(150, 600, 1)
        #       Aufrufreihenfolge data[algorithm][timestep]
        average_platoon_size = [[] for a in xrange(len(algorithms))]
        average_happiness = [[] for a in xrange(len(algorithms))]

        for a in range(len(algorithms)):
            for seed in seeds:
                full_path = scenario + "/" + seed + "/" + algorithms[a]

                platoon_size = csv_to_array(full_path + "/platoon_size.csv")
                happiness = csv_to_array(full_path + "/happiness.csv")

                for step in timesteps:
                    # for every line in array
                    if len(platoon_size) / 2 > step:
                        platoon_size_step = (platoon_size[step, 1:])
                        happiness_step = (happiness[step, 1:])
                        # amount of cars is actually the same
                        amount_of_cars = np.sum((platoon_size_step > -1))

                        platoon_leaders = np.sum((platoon_size_step > -1) & (platoon_size_step < 1000))
                        average_platoon_size[a].append(float(amount_of_cars) / platoon_leaders)

                        happiness_sum = sum(happiness_step) - amount_of_cars + len(happiness_step)
                        average_happiness[a].append(float(happiness_sum) / amount_of_cars)



        # append all timestep - lists to one list for boxplotting
        for a in range(len(algorithms)):
            platoon_size_data.append(average_platoon_size[a])
            happiness_data.append(average_happiness[a])
        # Gap between two time steps.
        platoon_size_data.append([])
        platoon_size_data.append([])
        happiness_data.append([])
        happiness_data.append([])
        labels.append(scenario[9:])
        print(labels)


    x_tick1 = np.arange(3, len(scenarios) * (len(algorithms) + 2) + 1, 7)
    x_tick2 = labels
    make_boxplot(path, x_tick1, x_tick2, platoon_size_data, 'Scenarios',
                 'Average Platoon Size', "Average Platoon Size Boxplot", (0.75, 3.5), colorize=True,
                 legend=algorithms, amount_of_bars=7)
    make_boxplot(path, x_tick1, x_tick2, happiness_data, 'Scenarios',
                 'Average Happiness', "Average Happiness Boxplot", (0.5, 0.9), colorize=True,
                 legend=algorithms, amount_of_bars=7)


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


def make_boxplot(path, x_tick1, x_tick2, platoon_size_data, xlabel, ylabel, title, ylim, colorize=False,
                 legend=None, amount_of_bars=1000):
    fig, ax = plt.subplots()
    fig.set_size_inches(14.5, 10.5)
    plt.title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_ylim(ylim)
    bp = ax.boxplot(platoon_size_data, showfliers=False)
    if colorize:
        legend = list(legend)
        for i in range(len(legend)):
            legend[i] = PLOTNAMES[legend[i]]
        colorize_bps(bp, threshold=amount_of_bars)
        ax.legend([bp["boxes"][0], bp["boxes"][1], bp["boxes"][2], bp["boxes"][3], bp["boxes"][4]], legend,
                  loc="best")

    plt.xticks(x_tick1, x_tick2)
    fig.savefig(path + "/" + title + ".png")
    plt.close()


def deleter(folder):
    scenarios = os.listdir(folder)
    for scenario in scenarios:
        if not (scenario.endswith(".png") or scenario.endswith(".txt")):
            seeds = os.listdir(folder + "/" + scenario)
            for seed in seeds:
                if not (seed.endswith(".png") or seed.endswith(".txt")):
                    algorithms = os.listdir(folder + "/" + scenario + "/" + seed)
                    for algorithm in algorithms:
                        if not (algorithm.endswith(".png") or algorithm.endswith(".txt")):
                            files = os.listdir(folder + "/" + scenario + "/" + seed + "/" + algorithm)
                            for file in files:
                                if not (file.startswith("happiness.csv") or file.startswith("platoon_size.csv")):
                                    os.remove(folder + "/" + scenario + "/" + seed + "/" + algorithm + "/" + file)
                        else:
                            os.remove(folder + "/" + scenario + "/" + seed + "/" + algorithm)
                else:
                    os.remove(folder + "/" + scenario + "/" + seed)


def main():
    plt.rc('font', size=MEDIUM_SIZE)  # controls default text sizes
    plt.rc('axes', titlesize=MEGA_SIZE)  # fontsize of the axes title
    plt.rc('axes', labelsize=MEGA_SIZE)  # fontsize of the x and y labels
    plt.rc('xtick', labelsize=BIGGER_SIZE)  # fontsize of the tick labels
    plt.rc('ytick', labelsize=BIGGER_SIZE)  # fontsize of the tick labels
    plt.rc('legend', fontsize=BIGGER_SIZE)  # legend fontsize
    plt.rc('figure', titlesize=MEGA_SIZE)  # fontsize of the figure title

    folder = "boxplots"

    deleter(folder)
    boxplots(folder)


if __name__ == "__main__":
    main()