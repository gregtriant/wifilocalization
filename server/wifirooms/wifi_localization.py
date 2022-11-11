import json
import requests
import math
import pandas as pd
from .wifi_radiomap import SignalPoint, RadioMap

from sklearn.neighbors import KNeighborsClassifier


class Localization:
    test_point = [{'BSSID': '78:96:82:3a:9d:c8', 'level': -42},
                  {'BSSID': '28:ff:3e:03:76:dc', 'level': -62},
                  {'BSSID': '62:ff:3e:03:76:dd', 'level': -65},
                  {'BSSID': 'f4:23:9c:20:9a:06', 'level': -75},
                  {'BSSID': '0c:b9:12:03:c4:20', 'level': -82},
                  {'BSSID': '08:26:97:e4:4f:51', 'level': -83},
                  {'BSSID': '50:78:b3:80:c4:bd', 'level': -86},
                  {'BSSID': '5a:d4:58:f2:8e:64', 'level': -87},
                  {'BSSID': '78:96:82:2f:ef:4e', 'level': -88},
                  {'BSSID': '62:96:82:2f:ef:4f', 'level': -89},
                  {'BSSID': '34:58:40:e6:60:c0', 'level': -92},
                  {'BSSID': '50:81:40:15:41:e8', 'level': -95}]

    def __init__(self, radio_map):
        self.radio_map = radio_map

    def find_room_knn(self, scanned_networks):
        x_train = self.radio_map.df_dataset.iloc[:, 3:]
        y_train = self.radio_map.df_dataset.iloc[:, 0]
        # print(self.radio_map.df_dataset.head())

        # make the classifiers
        knn3 = KNeighborsClassifier(n_neighbors=3)
        knn3.fit(x_train, y_train)

        networks = list(map(lambda net: (net["BSSID"], net["level"]), scanned_networks))
        networks = sorted(networks, key=lambda x: -x[1])

        networks = self.organize_rssi_of_new_point(networks, self.radio_map.unique_bssids_of_floor_plan)
        # networks_bssids = [x[0] for x in networks]

        df_test = self.convert_networks_to_df(networks, self.radio_map.unique_bssids_of_floor_plan)
        y_pred_knn3 = knn3.predict(df_test)
        print("Room prediction:", y_pred_knn3)
        return y_pred_knn3

    def knn(self, signal_points, test_point=None, k=4):
        print(' --> Localization with knn!')

        # we will use there to calc the distances
        # unique_bssids = self.find_unique_bssids(signal_points)
        # print("Found " + str(len(unique_bssids)) + " unique bssids: ",  unique_bssids)

        if test_point is None:
            test_point = self.test_point

        knns = []

        # - find the min Number of coordinates to be used
        # lets say that it is the number of coords of the test_point
        for index, signal_point in enumerate(signal_points):
            # print(index, signal_point["networks"])
            dist = self.calc_dist(test_point, signal_point)
            # print("dist:", dist)
            # save to neighbors
            new_neighbor = {"x": signal_point["x"], "y": signal_point["y"], "dist": dist}
            knns.append(new_neighbor)

        knns = sorted(knns, key=lambda d: d['dist'])
        # print("neighbors SORTED:", knns)
        # print(knns[0:k:1])
        return knns[0:k:1]

    def calc_dist(self, test_point, signal_point):
        dist = 0
        test_point = sorted(test_point, key=lambda network: network['level']) # reverse=True
        # print("\n\nTest POint:", test_point)
        networks_of_signal_point = json.loads(signal_point["networks"])
        # print("\n\n", test_point)
        # print("\n\n", networks_of_signal_point)
        networks_of_signal_point = list(map(lambda point: {"BSSID": point["BSSID"], "level": point["level"]}, networks_of_signal_point))
        networks_of_signal_point = sorted(networks_of_signal_point, key=lambda network: network['level']) # reverse=True
        # print("\nSignal POint:", networks_of_signal_point)
        # print(networks_of_signal_point)
        # find all the unique bssids in order to calc the distance
        unique_bssids = self.find_unique_bssids(test_point + networks_of_signal_point)
        # print("Found " + str(len(unique_bssids)) + " unique bssids: ",  unique_bssids)

        for bssid in unique_bssids:
            pos1 = -1
            pos2 = -1
            for index, TP_network in enumerate(test_point):  # check if this network exists in Test Point
                # print(TP_network)
                if bssid == TP_network["BSSID"]:
                    pos1 = index
            for SP_network in networks_of_signal_point:  # check if this network exists in Signal Point
                # print(SP_network)
                if bssid == SP_network["BSSID"]:
                    pos1 = index

            if pos1 != -1 and pos2 != -1:
                dist += (test_point[pos1]["level"] - networks_of_signal_point[pos2]["level"]) * (test_point[pos1]["level"] - networks_of_signal_point[pos2]["level"])
            elif pos1 != -1 and pos2 == -1:
                # dist += (test_point[pos1]["level"] - (-100)) * (test_point[pos1]["level"] - (-100))
                dist += test_point[pos1]["level"] * test_point[pos1]["level"]
            elif pos1 == -1 and pos2 != -1:
                # dist += (networks_of_signal_point[pos2]["level"] - (-100)) * (networks_of_signal_point[pos2]["level"] - (-100))
                dist += networks_of_signal_point[pos2]["level"] * networks_of_signal_point[pos2]["level"]

        return math.sqrt(dist)

    def find_unique_bssids(self, network_list):
        # print(json.loads(signal_points[0]['networks'])[0])
        unique_networks = []
        for network in network_list:
            # print(network['BSSID'])
            if network['BSSID'] not in unique_networks and network['level'] > -90:
                unique_networks.append(network['BSSID'])
        return unique_networks

    def dbm_to_quality(self, dbm):
        # where dBm: [-100 to - 50]
        quality = 0
        if dbm <= -100:
            quality = 0
        elif dbm >= -50:
            quality = 100
        else:
            quality = 2 * (dbm + 100)

        return quality

    def organize_rssi_of_new_point(self, scanned_networks, unique_bssids_of_floor_plan):
        # print(len(networks), networks)
        # remove unknown bssids from this scan
        indexes_to_remove = []
        for network_index, network in enumerate(scanned_networks):
            bssid = network[0]
            if bssid not in unique_bssids_of_floor_plan:
                # then we cannot use this network
                indexes_to_remove.append(network_index)

        new_networks = []
        for index, net in enumerate(scanned_networks):
            if index not in indexes_to_remove:
                new_networks.append(net)

        scanned_networks = new_networks.copy()
        del new_networks

        # print(len(networks), networks)
        # add the lowest value to as the value of the rest of the networks that were not scanned this time
        networks_bssids = [x[0] for x in scanned_networks]
        for unique_bssid in unique_bssids_of_floor_plan:
            if unique_bssid not in networks_bssids:
                scanned_networks.append((unique_bssid, SignalPoint.RSSI_LOWEST))
        # print(len(networks), networks)
        assert len(scanned_networks) == len(unique_bssids_of_floor_plan), "They should be of equal length to continue!"

        return scanned_networks

    def convert_networks_to_df(self, networks, unique_bssids_of_floor_plan):
        df_columns = unique_bssids_of_floor_plan.copy()
        df_test = pd.DataFrame(columns=df_columns)
        # print(df)
        new_df_row = {}
        for network in networks:
            # print(network)
            bssid = network[0]
            val = network[1]
            d = {
                bssid: [val]
            }
            new_df_row.update(d)
        # print(new_df_row)
        df_test = pd.concat([df_test, pd.DataFrame.from_dict(new_df_row)], ignore_index=True, axis=0)
        return df_test
