import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

r = requests.get('http://127.0.0.1:8000/static/data/big_room.csv')
# print(r.content)
data_str = r.content.decode("utf-8")  # r.content is in bytes format

df = pd.DataFrame([line.split(',') for line in data_str.split('\r\n')])
# print(df.head())
df['index'] = df.index

print(df.head())
times = df[0].tolist()
index = df['index'].tolist()

acc_x = [float(x or 0) for x in df[1].tolist()]
acc_y = [float(x or 0) for x in df[2].tolist()]
acc_z = [float(x or 0) for x in df[3].tolist()]

mag_x = [float(x or 0) for x in df[4].tolist()]
mag_y = [float(x or 0) for x in df[5].tolist()]
mag_z = [float(x or 0) for x in df[6].tolist()]

gyr_x = [float(x or 0) for x in df[7].tolist()]
gyr_y = [float(x or 0) for x in df[8].tolist()]
gyr_z = [float(x or 0) for x in df[9].tolist()]


plt.figure(1)
x_val = index
plt.plot(x_val, acc_x, color="r", linewidth=1, linestyle="dotted")
plt.plot(x_val, acc_y, color="g", linewidth=1, linestyle="dotted")
plt.plot(x_val, acc_z, color="b", linewidth=1, linestyle="dotted")

plt_title = "Accelerometer"
plt.title(plt_title)
plt.xlabel("Index")
plt.ylabel("Accel")
plt.legend(['acc_x', 'acc_y', 'acc_z'], loc='best')

plt.figure(2)
plt.plot(x_val, mag_x, color="r", linewidth=1, linestyle="dotted")
plt.plot(x_val, mag_y, color="g", linewidth=1, linestyle="dotted")
plt.plot(x_val, mag_z, color="b", linewidth=1, linestyle="dotted")

plt_title = "Magnetometer"
plt.title(plt_title)
plt.xlabel("Index")
plt.ylabel("Mag")
plt.legend(['mag_x', 'mag_y', 'mag_z'], loc='best')

plt.figure(3)
plt.plot(x_val, gyr_x, color="r", linewidth=1, linestyle="dotted")
plt.plot(x_val, gyr_y, color="g", linewidth=1, linestyle="dotted")
plt.plot(x_val, gyr_z, color="b", linewidth=1, linestyle="dotted")

plt_title = "Gyroscope"
plt.title(plt_title)
plt.xlabel("Index")
plt.ylabel("Gyr")
plt.legend(['gyr_x', 'gyr_y', 'gyr_z'], loc='best')