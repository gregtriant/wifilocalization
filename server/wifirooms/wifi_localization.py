import pandas as pd
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from .wifi_radiomap import SignalPoint, RadioMap

from sklearn.neighbors import KNeighborsClassifier


class Localization:
    names_of_classifiers = [
        "knn",
        "wknn",
        "linear_svm",
        "svm",
        "decision_tree",
        "random_forest",
        "MLP",
        "adaboost",
        "naive_bayes",
    ]

    point_classifiers = [
        KNeighborsClassifier(n_neighbors=3),
        KNeighborsClassifier(n_neighbors=5, weights='distance'),
        SVC(kernel="linear", C=0.025),
        SVC(gamma=2, C=1),
        DecisionTreeClassifier(max_depth=5),
        RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
        MLPClassifier(alpha=1, max_iter=3000),
        AdaBoostClassifier(),
        GaussianNB(),
    ]

    room_classifiers = [
        KNeighborsClassifier(n_neighbors=3),
        KNeighborsClassifier(n_neighbors=3, weights='distance'),
        SVC(kernel="linear", C=0.025),
        SVC(gamma=2, C=1),
        DecisionTreeClassifier(max_depth=5),
        RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
        MLPClassifier(alpha=1, max_iter=2000),
        AdaBoostClassifier(),
        GaussianNB(),
    ]

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
        self.make_room_classifiers()
        self.make_point_classifiers()

    def make_point_classifiers(self):
        # ['knn', 'linear_svm', 'svm', 'gaussian', 'naive_bayes', 'decision_tree', 'random_forest', 'MLP', 'adaboost'] # available algorithms
        print("Making point classifiers...")
        x_train = self.radio_map.df_dataset.iloc[:, 4:len(self.radio_map.unique_bssids_of_floor_plan) + 4:1]
        y_train = self.radio_map.df_dataset['point']
        if x_train.empty or y_train.empty:
            return
        # train the classifiers
        for name, clf in zip(self.names_of_classifiers, self.point_classifiers):
            clf.fit(x_train, y_train)


    def make_room_classifiers(self):
        print("Making room classifiers...")
        x_train = self.radio_map.df_dataset.iloc[:, 4:len(self.radio_map.unique_bssids_of_floor_plan) + 4:1]
        y_train = self.radio_map.df_dataset['room'] # the room column

        if x_train.empty or y_train.empty:
            return
        # train the classifiers
        for name, clf in zip(self.names_of_classifiers, self.room_classifiers):
            clf.fit(x_train, y_train)


    def find_point(self, scanned_networks, algorithm, probabilites=False):
        df_test = self.networks_to_df(scanned_networks)
        for name, clf in zip(self.names_of_classifiers, self.point_classifiers):
            # print(name, algorithm)
            if name == algorithm:
                if not probabilites:
                    y_pred = clf.predict(df_test)
                    # print("Point prediction:", int(y_pred[0]))
                    df = self.radio_map.df_dataset
                    df_row_result = df.loc[df['point'] == y_pred[0]]  # get just room and pointx, pointy columns of df
                    # print("result length:", len(df_row_result))
                    if len(df_row_result) > 0:
                        df_row_result = df_row_result.iloc[:1] # getting first row
                    # print(df_row_result)
                    result = {
                        'point': int(df_row_result['point'].iat[0]),
                        'room': df_row_result['room'].iat[0],
                        'x': float(df_row_result['pointX'].iat[0]),
                        'y': float(df_row_result['pointY'].iat[0])
                    }
                    return result
                elif probabilites:
                    y_pred = clf.predict_proba(df_test)
                    data = {
                        'classes': clf.classes_,
                        'y_pred': y_pred
                    }
                    return data


        return 'Algorith not supported'


    def find_room(self, scanned_networks, algorithm, probabilites=False):
        df_test = self.networks_to_df(scanned_networks)
        for name, clf in zip(self.names_of_classifiers, self.room_classifiers):
            if name == algorithm:
                if not probabilites:
                    y_pred = clf.predict(df_test)
                    return y_pred
                elif probabilites:
                    y_pred = clf.predict_proba(df_test)
                    data = {
                        'classes': clf.classes_,
                        'y_pred': y_pred
                    }
                    return data

        return 'algorithm not supported'


    def networks_to_df(self, scanned_networks):
        networks = list(map(lambda net: (net["BSSID"], net["level"]), scanned_networks))
        networks = sorted(networks, key=lambda x: -x[1])
        networks = self.organize_rssi_of_new_point(networks, self.radio_map.unique_bssids_of_floor_plan)  # add the rest of the bssids that are unique to the radio map
        df_test = self.convert_networks_to_df(networks, self.radio_map.unique_bssids_of_floor_plan)  # convert to dataframe
        return df_test


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


# OLD KNN with actual dist
    # def knn(self, signal_points, test_point=None, k=4):
# neighbors = []

# for index, sp in enumerate(self.radio_map.signal_points):
#     # print(index)
#     dist = 0
#     for net in sp.fingerprint:
#         bssid = net[0]
#         mean_rssi = net[2]
#         dist += (mean_rssi - df_test[bssid].iat[0]) * (mean_rssi - df_test[bssid].iat[0])
#
#     new_neighbor = {"x": sp.x, "y": sp.y, "dist": dist}
#     neighbors.append(new_neighbor)
#
# neighbors = sorted(neighbors, key=lambda d: d['dist'])
# return neighbors[0:3:1]