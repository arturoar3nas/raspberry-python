#!/usr/bin/python3

import subprocess
import json
import re

path = dict()
path['net'] = '/home/pi/servicecom/networks.json'


def getWiFiList():
    """Get a list of WiFi networks"""

    proc = subprocess.Popen('iwlist scan 2>/dev/null', shell=True, stdout=subprocess.PIPE, )
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
            network["mac"] = match.group(1)

        match = re.search('ESSID:"(\S+)"', line)
        if match:
            network["ssid"] = match.group(1)

        # Quality=31/70  Signal level=-79 dBm
        match = re.search('Quality=([0-9]+)\/([0-9]+)[ \t]+Signal level=([0-9-]+) dBm', line)
        if match:
            network["quality"] = match.group(1)
            network["quality@scale"] = match.group(2)
            network["dbm"] = match.group(3)

        # Encryption key:on
        match = re.search('Encryption key:(on|.+)', line)
        if match:
            network["encryption"] = match.group(1)

        # Channel:1
        match = re.search('Channel:([0-9]+)', line)
        if match:
            network["channel"] = match.group(1)

        # Frequency:2.412 GHz (Channel 1)
        match = re.search('Frequency:([0-9\.]+) GHz', line)
        if match:
            network["freq"] = match.group(1)

    if len(network):
        networks.append(network)

    strjson = json.dumps(networks, indent=4, sort_keys=True)
    fjson = open(path['net'], "w+")
    fjson.write(strjson)
    fjson.close()


if __name__ == "__main__":
    getWiFiList()