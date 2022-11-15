import requests
import json
import math
import matplotlib.pyplot as plt
import numpy as np
import statistics

show_dbm_of_scan = True


class SignalPoint:

    def __init__(self, x, y, scan1):
        self.x = x
        self.y = y
        self.scans = [scan1.copy()]

    def add_scan(self, scan1):
        self.scans.append(scan1)


print('plotting wifi points')
signal_points = []

r = requests.get('http://127.0.0.1:8000/api/signalPoints?floor_plan_id=1')

points = json.loads(r.text)

# for each scan we see the coordinates and group them to single points. One point has a number of scans
for index, point in enumerate(points):
    # print(index, point['networks'])
    found_it = False
    for i in range(0, len(signal_points)):
        if math.isclose(signal_points[i].x, point['x']) and math.isclose(signal_points[i].y, point['y']):  # found same point
            # add networks
            # temp = json.loads(point['networks']).copy()
            signal_points[i].add_scan(json.loads(point['networks']))
            found_it = True
            break

    if found_it is False:
        # add new sp
        sp = SignalPoint(point['x'], point['y'], json.loads(point['networks']))
        signal_points.append(sp)

print('Found ', len(signal_points), 'different points')

# chose a point
signal_point = signal_points[0]

print(signal_point.x, signal_point.y)

# find the unique bssids that were found during the 40 scans on this point
# we need to do this because not all the bssids appear in each scan. some may be less frequent
unique_bssids = []
for index, scan in enumerate(signal_point.scans):
    # print(index, scan)
    for network in scan:
        # print(network)
        if (network['BSSID'], network['SSID']) not in unique_bssids:
            unique_bssids.append((network['BSSID'], network['SSID']))

print(unique_bssids, "\n")

# for each unique bssid get the ssi level and plot it against time (40 scans)
chosen_ssids = []
for unique_net in unique_bssids:
    bssid = unique_net[0]
    ssid = unique_net[1]
    signal_strengths = []
    freq = 0
    for index, scan in enumerate(signal_point.scans):
        for network in scan:
            if network['BSSID'] == bssid:  # check if this bssid was found in that scan
                signal_strengths.append((index, network['level']))

    freq = len(signal_strengths) / len(signal_point.scans)  # number of times this bssid appeared during the 40 scans
    print(bssid, ssid, ' freq:', "{:6.4f}".format(freq), signal_strengths)
    if freq >= 0.7:
        chosen_ssids.append(ssid)
        if show_dbm_of_scan:
            plt.figure()

            # plot mean
            dbm_vals = [x[1] for x in signal_strengths]  # get second value of tuples
            # print(dbm_vals)
            mean = np.mean(dbm_vals)
            std = np.std(dbm_vals)
            var = np.var(dbm_vals)
            mode = statistics.mode(dbm_vals)  # mode is the most frequent value of the array
            mean_arr = np.repeat(mean, 85)
            mode_arr = np.repeat(mode, 85)
            x_val = np.arange(0, 85, 1)
            plt.plot(x_val, mean_arr, color="r", linewidth=1, linestyle="dotted")
            plt.plot(x_val, mode_arr, color="g", linewidth=1, linestyle="dotted")
            plt.figtext(.15, .15, "Mean: " + str(format(mean, ".2f")) +
                        "\nVar: " + str(format(var, ".2f")) +
                        "\nStd: " + str(format(std, ".2f")) +
                        "\nMode: " + str(mode))
            # plot all the points
            # plt.scatter(*zip(*signal_strengths), s=10)
            plt.plot(*zip(*signal_strengths), marker='.', markersize=7, linewidth=1)
            plt.xlim(-1, 87)
            plt.ylim(-100, -35)
            plt_title = "Levels for: " + bssid + " " + ssid
            plt.title(plt_title)
            plt.xlabel("Scan Number")
            plt.ylabel("dBm level")
            plt.legend(['mean', 'mode'], loc='best')

            # collective Figure
            plt.figure(100)
            plt.plot(*zip(*signal_strengths), marker='.', markersize=7, linewidth=1)
            plt.xlim(-1, 87)
            plt.ylim(-100, -35)
            plt.xlabel("Scan Number")
            plt.ylabel("dBm level")
            plt.legend(chosen_ssids, loc='best')

plt.show()
