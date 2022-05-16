import requests
import json
import matplotlib.pyplot as plt
import numpy as np


def p2f(x):  # x is type string
    return float(x.strip('%')) / 100


print('plotting wifi points')
r = requests.get('http://127.0.0.1:8000/api/floorPlans/1/')
r_dict = json.loads(r.text)
signal_points = r_dict["signal_points"]
#
# print(type(r.text))
# print(r.text)
#
# print(r_dict)
a = np.zeros((581, 600))
numRows, numCols = a.shape
print("Rows: ", numRows, "Cols: ", numCols)

i = 0
for point in signal_points:
    x = point['x']
    y = point['y']
    print(i, ":", (x, y))
    networks = json.loads(point["networks"])
    for network in networks:
        if network["ssid_name"] == "COSMOTE":
            bssid_list = network["bssid_list"]
            signalStrength = bssid_list[0]["rssi"]
            signalStrength = p2f(signalStrength)
            print(signalStrength)
            a[y][x] = signalStrength
    i += 1
    # a[x][y] =
    # print(point["networks"])

# print(signal_points)
# plt.figure()
# plt.axis([0, 581, 0, 600])
# plt.grid(False)                         # set the grid

# ax = plt.gca()                            # get the axis
# ax.set_ylim(ax.get_ylim()[::-1])        # invert the axis
# ax.xaxis.tick_top()                     # and move the X-Axis
# ax.yaxis.set_ticks(np.arange(0, 16, 1)) # set y-ticks
# ax.yaxis.tick_left()                    # remove right y-Ticks

plt.imshow(a, cmap='hot', interpolation='nearest')
# plt.plot(a)
plt.show()
plt.close("all")
