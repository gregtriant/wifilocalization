import requests
import json
import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import statistics
import random
import scipy.stats as stats

from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn import metrics
from sklearn.metrics import mean_squared_error

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class SignalPoint:
    RSSI_LOWEST = -100  # dBm

    def __init__(self, x, y, scan1, fingerprint=[], room=""):
        self.x = x
        self.y = y
        self.scans = [scan1.copy()]
        self.fingerprint = fingerprint.copy()
        self.room = room

    def add_scan(self, scan1):
        self.scans.append(scan1)

    def set_room_of_point(self, room):
        self.room = room

    def set_fingerprint(self, fingerprint):
        self.fingerprint = fingerprint.copy()


class RadioMap:
    unique_bssids_of_floor_plan = []
    signal_points = []
    df_dataset = []
    rooms = []

    def __init__(self, points_from_database, rooms_from_database):
        self.rooms = rooms_from_database
        # for each scan we see the coordinates and group them to single points. One point has a number of scans
        for index, point in enumerate(points_from_database):
            # print(index, point['networks'])
            found_it = False
            for i in range(0, len(self.signal_points)):
                width = 600 # example width and height just to upscale the points
                height = 581
                point1_x = math.floor(self.signal_points[i].x * width)
                point2_x = math.floor(point['x'] * width)

                point1_y = math.floor(self.signal_points[i].y * height)
                point2_y = math.floor(point['y'] * height)
                if point1_x == point2_x and point1_y == point2_y:  # found same point
                    # add networks
                    self.signal_points[i].add_scan(json.loads(point['networks']))
                    found_it = True
                    break

            if found_it is False:
                # add new sp
                sp = SignalPoint(point['x'], point['y'], json.loads(point['networks']))
                self.find_room_of_point(sp)
                self.signal_points.append(sp)

        del points_from_database
        print('Found ', len(self.signal_points), 'different points')



    def find_room_of_point(self, sp):
        for room in self.rooms:
            if room["x"] < sp.x and sp.x < room["x"] + room["width"] and room["y"] < sp.y and sp.y < room["y"] + room["height"]:
                sp.set_room_of_point(room["name"])
                # print(sp.room)
                break

    def make_radio_map(self):
        for index, signal_point in enumerate(self.signal_points):
            # print("-------------------------------------------------")
            # print(str(index) + ")", signal_point.x, signal_point.y)
            # find the unique bssids that were found during the 40 scans on this point
            # we need to do this because not all the bssids appear in each scan. some may be less frequent
            unique_bssids_of_point = []
            for scan in signal_point.scans:
                # print(index, scan)
                for network in scan:
                    # print(network)
                    if network['BSSID'] not in unique_bssids_of_point:
                        unique_bssids_of_point.append(network['BSSID'])

            # print("Found", len(unique_bssids_of_point), "unique bssids.", unique_bssids_of_point)

            signal_point_fingerprint = []
            for bssid in unique_bssids_of_point:
                # print(bssid, ssid)
                signal_strengths = []
                freq = 0
                for scan_index, scan in enumerate(signal_point.scans):
                    for network in scan:
                        if network['BSSID'] == bssid:  # check if this bssid was found in that scan
                            signal_strengths.append((scan_index, network['level']))

                freq = len(signal_strengths) / len(signal_point.scans)  # number of times this bssid appeared during the 40 scans

                if freq >= 0.7:  # excluding bssids that are not so often
                    dbm_vals = [x[1] for x in signal_strengths]  # get second value of tuples
                    # print(dbm_vals)
                    mean = np.mean(dbm_vals)
                    std = np.std(dbm_vals)
                    var = np.var(dbm_vals)
                    mode = statistics.mode(dbm_vals)  # mode is the most frequent value of the array
                    # print(f'{bssid:<20}', f'{ssid:<35}', 'f:', "{:6.4f}".format(freq), "m:", "{:6.4f}".format(mean),
                    # "std:", "{:6.4f}".format(std), "mode:", "{:6.4f}".format(mode), signal_strengths)
                    signal_point_fingerprint.append((bssid, freq, mean, std, mode))

            # sort the fingerprint
            signal_point.set_fingerprint(sorted(signal_point_fingerprint, key=lambda x: -x[2]))  # 0:bssid, 1:freq, 2:mean, 3:std, 4:mode # the minus sorts in descending order
            # print("Fingerpint kept:", len(signal_point.fingerprint))
            # print(signal_point.fingerprint)

        # find unique BSSIDS in all signal_points
        self.unique_bssids_of_floor_plan = []
        for signal_point in self.signal_points:
            # find the unique bssids that appear in all fingerprints of the floor plan
            for network in signal_point.fingerprint:
                bssid = network[0]
                # bssids = [x[0] for x in self.unique_bssids_of_floor_plan]
                if bssid not in self.unique_bssids_of_floor_plan:
                    self.unique_bssids_of_floor_plan.append(bssid)

        print("Found", len(self.unique_bssids_of_floor_plan), "unique and useful bssids for this floor plan.")
        # print(self.unique_bssids_of_floor_plan)

        # at each point, if a bssid is not found, we place the lowest level as its value
        for index, signal_point in enumerate(self.signal_points):
            # find the unique bssids that appear in all fingerprints of the floor plan
            for bssid in self.unique_bssids_of_floor_plan:
                found = False
                for network in signal_point.fingerprint:
                    if network[0] == bssid:
                        found = True
                        break
                if not found:
                    signal_point.fingerprint.append((bssid, 1, signal_point.RSSI_LOWEST, 0, signal_point.RSSI_LOWEST))  # 0:bssid, 1:freq, 2:mean, 3:std, 4:mode



        # make a dataframe for the dataset
        df_colums = self.unique_bssids_of_floor_plan.copy()
        df_colums.insert(0, "pointX")
        df_colums.insert(1, "pointY")
        df_colums.insert(0, "room")
        df = pd.DataFrame(columns=df_colums)
        # print(df)
        for index, sp in enumerate(self.signal_points):
            # print(sp.room)
            new_df_row = {}
            new_df_row.update({'pointX': [sp.x]})
            new_df_row.update({'pointY': [sp.y]})
            new_df_row.update({'room': [sp.room]})

            for network in sp.fingerprint:
                bssid = network[0]
                mean = network[2]
                d = {
                    bssid: mean
                }
                new_df_row.update(d)
            # print(new_df_row)
            df = pd.concat([df, pd.DataFrame.from_dict(new_df_row)], ignore_index=True, axis=0)

        self.df_dataset = df



#
# # Fixing random state for reproducibility
# np.random.seed(19680801)
#
# width = 600
# height = 581
#
#
#
# fig = plt.figure()
# ax = fig.add_subplot(projection='3d')
# x, y = np.random.rand(2, 100) * 4
# # print(x)
# hist, xedges, yedges = np.histogram2d(x, y, bins=4, range=[[0, 4], [0, 4]])
#
# # Construct arrays for the anchor positions of the 16 bars.
# xpos, ypos = np.meshgrid(xedges[:-1] + 0.25, yedges[:-1] + 0.25, indexing="ij")
# xpos = xpos.ravel()
# ypos = ypos.ravel()
# zpos = 0
#
# # Construct arrays with the dimensions for the 16 bars.
# dx = dy = 0.5 * np.ones_like(zpos)
# dz = hist.ravel()
#
# ax.bar3d(xpos, ypos, zpos, dx, dy, dz, zsort='average')
#
# plt.show()
#
#
# print("Getting points of Floorplan...")
# res = requests.get('http://127.0.0.1:8000/api/signalPoints?floor_plan_id=1')
# points = json.loads(res.text)
# print("Done!")
# print("Getting rooms of Floorplan...")
# res = requests.get('http://127.0.0.1:8000/api/rooms?floor_plan_id=1')
# rooms = json.loads(res.text)
# print("Done!")
# print(rooms)
#
# rm = RadioMap(points, rooms)
# rm.make_radio_map()
#
# print(rm.df_dataset.head())
#
# print()
# ax1 = fig.add_subplot(projection='3d')
#
# x3 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
# y3 = [5, 6, 7, 8, 2, 5, 6, 3, 7, 2]
# z3 = np.zeros(10)
#
# dx = np.ones(10)
# dy = np.ones(10)
# dz = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
#
#
# ax1.bar3d(y3, x3, z3, dx, dy, dz, color="red")
# # ax1.axis('off')
# plt.show()

# def find_room_of_point(point, rooms):
#     for room in rooms:
#         if room["x"] < point.x and point.x < room["x"] + room["width"] and room["y"] < point.y and point.y < room["y"] + room["height"]:
#             sp.set_room_of_point(room["name"])
#             print(sp.room)
#             break

# def organize_rssi_of_new_point(scanned_networks, unique_bssids_of_floor_plan):
#     # print(len(networks), networks)
#     # remove unknown bssids from this scan
#     indexes_to_remove = []
#     for network_index, network in enumerate(scanned_networks):
#         bssid = network[0]
#         if bssid not in unique_bssids_of_floor_plan:
#             # then we cannot use this network
#             indexes_to_remove.append(network_index)
#
#     new_networks = []
#     for index, net in enumerate(scanned_networks):
#         if index not in indexes_to_remove:
#             new_networks.append(net)
#
#     scanned_networks = new_networks.copy()
#     del new_networks
#
#     # print(len(networks), networks)
#     # add the lowest value to as the value of the rest of the networks that were not scanned this time
#     networks_bssids = [x[0] for x in networks]
#     for unique_bssid in unique_bssids_of_floor_plan:
#         if unique_bssid not in networks_bssids:
#             scanned_networks.append((unique_bssid, SignalPoint.RSSI_LOWEST))
#     # print(len(networks), networks)
#     assert len(scanned_networks) == len(unique_bssids_of_floor_plan), "They should be of equal length to continue!"
#
#     return scanned_networks
#
#
# def convert_networks_to_df(networks, unique_bssids_of_floor_plan):
#     df_columns = unique_bssids_of_floor_plan.copy()
#     df_test = pd.DataFrame(columns=df_columns)
#     # print(df)
#     new_df_row = {}
#     for network in networks:
#         # print(network)
#         bssid = network[0]
#         val = network[1]
#         d = {
#             bssid: [val]
#         }
#         new_df_row.update(d)
#     # print(new_df_row)
#     df_test = pd.concat([df_test, pd.DataFrame.from_dict(new_df_row)], ignore_index=True, axis=0)
#     return df_test

# print("Getting points of Floorplan...")
# res = requests.get('http://127.0.0.1:8000/api/signalPoints?floor_plan_id=1')
# points = json.loads(res.text)
# print("Done!")
# print("Getting rooms of Floorplan...")
# res = requests.get('http://127.0.0.1:8000/api/rooms?floor_plan_id=1')
# rooms = json.loads(res.text)
# print("Done!")
# print(rooms)
#
# rm = RadioMap(points, rooms)
# rm.make_radio_map()
#
# # print(rm.df_dataset)
# X_train = rm.df_dataset.iloc[:, 3:]
# Y_train = rm.df_dataset.iloc[:, 0]
# print(rm.df_dataset.head())
#
# # make the classifiers
# knn3 = KNeighborsClassifier(n_neighbors=3)
# knn3.fit(X_train, Y_train)
#
# naive_bayes = GaussianNB()
# naive_bayes.fit(X_train, Y_train)
#
# y_test = []
# y_pred_knn = []
# y_pred_nb = []
#
# # test existing scans against the fingerprints
# for signal_point_index, signal_point in enumerate(rm.signal_points):
#     # select a random scan from this point
#     scan_number = random.randint(0, len(signal_point.scans)-1)
#     # print("Signal_point:", signal_point_index, "x:", signal_point.x, "y:", signal_point.y, "Randomly selected scan:", scan_number)
#     # print("point of room:", signal_point.room)
#     y_test.append(signal_point.room)
#
#     networks = signal_point.scans[scan_number].copy()
#     networks = list(map(lambda point: (point["BSSID"], point["level"]), networks))
#     networks = sorted(networks, key=lambda x: -x[1])
#
#     networks = organize_rssi_of_new_point(networks, rm.unique_bssids_of_floor_plan)
#     # networks_bssids = [x[0] for x in networks]
#
#     df_test = convert_networks_to_df(networks, rm.unique_bssids_of_floor_plan)
#     # print(df_test)
#     # Use knn to find room of point
#     y_pred_knn3 = knn3.predict(df_test)
#     y_pred_knn.append(y_pred_knn3)
#     # print("knn:", y_pred_knn3)
#
#
#     y_pred_nb5 = naive_bayes.predict(df_test)
#     y_pred_nb.append(y_pred_nb5)
#     # print("naive_bayes:", y_pred_nb5)
#
#     # compare the scan with all points of the radio map
#     # scan_dbms = [x[1] for x in networks]
#     # kendall_taus = []
#     # for sp in rm.signal_points:
#     #     # print(sp.fingerprint)
#     #     signal_point_mean_dbms = [x[2] for x in sp.fingerprint]
#     #     # signal_point_mode_dbms = [x[4] for x in sp.fingerprint]
#     #     tau, p_value = stats.kendalltau(scan_dbms, signal_point_mean_dbms)
#     #     kendall_taus.append((sp, tau))
#     #
#     # kendall_taus = sorted(kendall_taus, key=lambda x: -x[1])
#     # for data in kendall_taus:
#     #     sp = data[0]
#     #     tau = data[1]
#     #     print(sp.x, sp.y, tau)
#
#     # send the point to all Connected Browsers
#     # channel_layer = get_channel_layer()
#     # async_to_sync(channel_layer.group_send)("browsers", {
#     #     "type": "robot.location",
#     #     "data": data
#     # })
#     # input("Press Enter to Continue to next point...")
#
#
# print("Accuracy KNN3:", metrics.accuracy_score(y_test, y_pred_knn))
# print("Accuracy NAIVE_BAYES:", metrics.accuracy_score(y_test, y_pred_nb))
#
# quit()







