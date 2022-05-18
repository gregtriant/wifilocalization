import json
import requests
import math


class Localization():
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

#
# Loc = Localization()
# Loc.knn()