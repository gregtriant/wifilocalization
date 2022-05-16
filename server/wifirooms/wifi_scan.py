import subprocess
import time
import sys

class WifiScaner():
    ssids = []
    current = {
        'ssid_name': '',
        'bssid_list': []
    }

    current_bssid = {
        'bssid': '',
        'rssi': ''
    }

    def scan(self):
        self.ssids = []
        self.current = {
            'ssid_name': '',
            'bssid_list': []
        }
        self.current_bssid = {
            'bssid': '',
            'rssi': ''
        }
        print('Scaning Wifi Networks...')
        start = time.time()
        results = []
        try:
            results = subprocess.check_output(["wifi", "scan"])
            results = results.decode("ascii")
        except:
            print("Error: Wifi Subprocess Failed!", sys.exc_info())
            return []

        results_list = results.split("\n")

        for ss in results_list:
            if ss.find('SSID') == 0:  # if you find a sting that STARTS with SSID
                # print(ss)
                if self.current["ssid_name"] != "":
                    if self.current_bssid["bssid"] != "":
                        self.current["bssid_list"].append(self.current_bssid)
                        self.current_bssid = {
                            'bssid': '',
                            'rssi': ''
                        }
                    self.ssids.append(self.current)
                    self.current = {
                        'ssid_name': '',
                        'bssid_list': []
                    }
                alist = ss.split(' ')
                self.current["ssid_name"] = alist[3].replace('\r', '', 1)

            elif ss.find('BSSID') != -1:  # if the string has BSSID
                # print(ss)
                if self.current_bssid["bssid"] != "":
                    self.current["bssid_list"].append(self.current_bssid)
                    self.current_bssid = {
                        'bssid': '',
                        'rssi': ''
                    }
                alist = ss.split(' ')
                self.current_bssid["bssid"] = alist[23].replace('\r', '', 1)

            elif ss.find('Signal') != -1:
                # print(ss)
                alist = ss.split(' ')
                self.current_bssid["rssi"] = alist[23]

        #  end of for loop, check if i have a last Ssid to put in the list.
        if self.current["ssid_name"] != "":
            if self.current_bssid["bssid"] != "":
                self.current["bssid_list"].append(self.current_bssid)
            self.ssids.append(self.current)

        end = time.time()
        print('Finished in: ', round((end-start), 2), 'seconds')
        return self.ssids


# networks = WifiScaner().scan()
# print(networks)
#
# for ssid in networks:
#     print(ssid["ssid_name"])
