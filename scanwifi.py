#!/usr/bin/python3

import subprocess
import json
import re
import os

"""
# @file   scanwifi.py
# @author Arturo Arenas (arturoar3nas@gmail.com)
# @date   12/06/18
# Brief:
    Scan wifi networks
  Usage:
    sudo python3 scanwifi.py
"""

path = dict()
path['net'] = '/home/pi/servicecom/networks.json'
path['config'] = '/home/pi/servicecom/config.json'


def load(path):
    try:
        with open(path) as f:
            data = json.load(f)
            f.close()
            return data
    except IOError as e:
        print("I/O error({0}): {1}".format(e.errno, e.strerror))
    except ValueError:
        print("Could not convert data to an integer.")
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
    return

def getWiFiList():
    """Get a list of WiFi networks"""
    data = load(path['config'])
    status_wifi = None
    if data['Flag']['Wifi'] == "0":
        os.system("sudo ifconfig wlan0 up")
        status_wifi = True

    proc = subprocess.Popen('sudo iwlist scan 2>/dev/null', shell=True, stdout=subprocess.PIPE, )
    stdout_str = proc.communicate()[0]
    stdout_list = stdout_str.decode().split('\n')
    networks = []

    network = {}
    for line in stdout_list:
        line = line.strip()
        match = re.search('Address: (\S+)', line)
        if match:
            if len(network):
                networks.append(network)
            network = {}
            network["Mac"] = match.group(1)

        match = re.search('ESSID:"(\S+)"', line)
        if match:
            network["SSID"] = match.group(1)

        # Quality=31/70  Signal level=-79 dBm
        match = re.search('Quality=([0-9]+)\/([0-9]+)[ \t]+Signal level=([0-9-]+) dBm', line)
        if match:
            network["Calidad"] = match.group(1)
            network["Calidad/Escala"] = match.group(2)
            network["Dbm"] = match.group(3)

        # Encryption key:on
        match = re.search('Encryption key:(on|.+)', line)
        if match:
            network["Encriptado"] = match.group(1)

        # Channel:1
        match = re.search('Channel:([0-9]+)', line)
        if match:
            network["Canal"] = match.group(1)

        # Frequency:2.412 GHz (Channel 1)
        match = re.search('Frequency:([0-9\.]+) GHz', line)
        if match:
            network["Frecuencia"] = match.group(1)

    if len(network):
        networks.append(network)

    strjson = json.dumps(networks, indent=4, sort_keys=True)
    fjson = open(path['net'], "w+")
    fjson.write(strjson)
    fjson.close()
    if status_wifi is True:
        itsalive = True
        while itsalive:
            os.system("sudo ifconfig wlan0 down")
            proc = subprocess.Popen('sudo ifconfig', shell=True, stdout=subprocess.PIPE, )
            stdout_str = proc.communicate()[0]
            stdout_list = stdout_str.decode().split('\n')
            for line in stdout_list:
                line = line.strip()
                match = re.search('wlan0: (\S+)', line)
                if match:
                    continue
                else:
                    itsalive = False
                    break

if __name__ == "__main__":
    getWiFiList()