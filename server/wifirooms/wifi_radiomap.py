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
    FIRST_SCANS_NUM = 40
    SECOND_SCANS_NUM = 40
    unique_bssids_of_floor_plan = []
    signal_points = []
    df_dataset = []
    rooms = []

    def __init__(self, points_from_database, rooms_from_database, limit_scans='all', take_average=True):
        self.rooms = rooms_from_database
        self.signal_points = []
        if limit_scans == 'all':
            self.SCAN_START = 0
            self.SCAN_END = self.FIRST_SCANS_NUM + self.SECOND_SCANS_NUM
        elif limit_scans == 'first':
            self.SCAN_START = 0
            self.SCAN_END = self.FIRST_SCANS_NUM
        elif limit_scans == 'second':
            self.SCAN_START = self.FIRST_SCANS_NUM
            self.SCAN_END = self.FIRST_SCANS_NUM + self.SECOND_SCANS_NUM

        if take_average:
            self.TAKE_AVERAGE = True
        else:
            self.TAKE_AVERAGE = False

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
                if abs(point1_x-point2_x) <= 2 and abs(point1_y-point2_y) <=2:  # found same point
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

    def add_scan_to_radio_map(self, x, y, networks): # this function exists so that we dont have to reconstuct the radio
                                                     # map every time we add a new scan.
        found_it = False
        for i in range(0, len(self.signal_points)):
            width = 600  # example width and height just to upscale the points
            height = 581
            point1_x = math.floor(self.signal_points[i].x * width)
            point2_x = math.floor(x * width)

            point1_y = math.floor(self.signal_points[i].y * height)
            point2_y = math.floor(y * height)
            if abs(point1_x - point2_x) <= 2 and abs(point1_y - point2_y) <= 2:  # found same point
                # add networks
                self.signal_points[i].add_scan(json.loads(networks))
                found_it = True
                break

        if found_it is False:
            # add new sp
            sp = SignalPoint(x, y, json.loads(networks))
            self.find_room_of_point(sp)
            self.signal_points.append(sp)

    def find_room_of_point(self, sp):
        for room in self.rooms:
            if room["x"] < sp.x and sp.x < room["x"] + room["width"] and room["y"] < sp.y and sp.y < room["y"] + room["height"]:
                sp.set_room_of_point(room["name"])
                # print(sp.room)
                break

    def make_radio_map(self):
        for index, signal_point in enumerate(self.signal_points): # all 129 signal points
            # find the unique bssids that were found during the 40 scans on this point
            # we need to do this because not all the bssids appear in each scan. some may be less frequent
            unique_bssids_of_point = []
            for i in range(self.SCAN_START, self.SCAN_END):
                scan = signal_point.scans[i]
                # print(i, ')', len(scan), scan)
                for network in scan:
                    # print(network)
                    if network['BSSID'] not in unique_bssids_of_point:
                        unique_bssids_of_point.append(network['BSSID'])

            # print("Found", len(unique_bssids_of_point), "unique bssids.", unique_bssids_of_point)

            signal_point_fingerprint = []
            for bssid in unique_bssids_of_point:
                # print("BSSID:", bssid)
                signal_strengths = []
                freq = 0
                for scan_index in range(self.SCAN_START, self.SCAN_END):
                    scan = signal_point.scans[scan_index]
                    # print(scan_index, ')', len(scan), scan)
                    for network in scan:
                        if network['BSSID'] == bssid:  # check if this bssid was found in that scan
                            signal_strengths.append((scan_index, network['level']))
                            freq += 1

                freq = freq / (self.SCAN_END - self.SCAN_START)  # number of times this bssid appeared during the N scans
                # print(bssid, freq, signal_strengths)
                if freq >= 0.7:  # excluding bssids that are not so often
                    dbm_vals = [x[1] for x in signal_strengths]  # get second value of tuples
                    # print(dbm_vals)
                    mean = np.mean(dbm_vals)
                    std = np.std(dbm_vals)
                    var = np.var(dbm_vals)
                    mode = statistics.mode(dbm_vals)  # mode is the most frequent value of the array
                    # print(f'{bssid:<20}', 'f:', "{:6.4f}".format(freq), "m:", "{:6.4f}".format(mean),
                    # "std:", "{:6.4f}".format(std), "mode:", "{:6.4f}".format(mode), signal_strengths)
                    signal_point_fingerprint.append((bssid, freq, mean, std, mode))

            # sort the fingerprint
            signal_point.set_fingerprint(sorted(signal_point_fingerprint, key=lambda x: -x[2]))  # 0:bssid, 1:freq, 2:mean, 3:std, 4:mode # the minus sorts in descending order
            # print("Fingerpint kept:", len(signal_point.fingerprint))
            # print("--------- ", index, "FINGERPRINT:", signal_point.fingerprint)

        # find unique BSSIDS in all signal_points
        self.unique_bssids_of_floor_plan = []
        for signal_point in self.signal_points:
            # find the unique bssids that appear in all fingerprints of the floor plan
            for network in signal_point.fingerprint:
                bssid = network[0]
                # bssids = [x[0] for x in self.unique_bssids_of_floor_plan]
                if bssid not in self.unique_bssids_of_floor_plan:
                    self.unique_bssids_of_floor_plan.append(bssid)
                    # TODO add a new list of the SSID for that BSSID

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
        df_columns = self.unique_bssids_of_floor_plan.copy()
        df_columns.insert(0, "point")
        df_columns.insert(1, "pointX")
        df_columns.insert(2, "pointY")
        df_columns.insert(3, "room")
        df = pd.DataFrame(columns=df_columns)
        # print(df)
        for index, sp in enumerate(self.signal_points):
            # print(sp.room)
            new_df_row = {}
            new_df_row.update({'point': str(index)})
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

        print(df.head())
        self.df_dataset = df








