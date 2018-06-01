#!/usr/bin/python3

# Copyright 2015-2017 Zack Scholl. All rights reserved.
# Use of this source code is governed by a AGPL
# license that can be found in the LICENSE file.

import sys
import os
import json
import argparse
import urllib.parse as urlparse
import logging
import string
import time
import requests
import RPi.GPIO as GPIO
import time

print("servicecom start")

# create logger with 'spam_application'
logger = logging.getLogger('cluster.py')
logger.setLevel(logging.DEBUG)




GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT) ## GPIO 17 como salida
GPIO.setup(27, GPIO.OUT) ## GPIO 27 como salida




def main(args, config):
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="config.json",
        help="location to configuration file")
    parser.add_argument(
        "-l",
        "--location",
        type=str,
        default="",
        help="location to use, for learning")
    parser.add_argument(
        "-u",
        "--user",
        type=str,
        default="",
        help="user to use, for learning")
    parser.add_argument(
        "-g",
        "--group",
        type=str,
        default="",
        help="group to use")
    parser.add_argument("command", type=str, default="",
                        help="start stop status track learn")
    args = parser.parse_args()

    # create file handler which logs even debug messages
    fh = logging.FileHandler('servicecom.log')
    ch = logging.StreamHandler()
    if args.debug:
        fh.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    else:
        fh.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(funcName)s:%(lineno)d - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    config = {}
    if not os.path.exists(args.config):
        pis = []
        while True:
            pi = input('Enter Pi address (e.g. pi@192.168.1.2. Enter blank if no more): ')
            if len(pi) == 0:
                break
            notes = input('Enter Pi notes (for you to remember): ')
            wlan = input('Which wlan to use (default: wlan1)?: ')
            if len(wlan) == 0:
                wlan = "wlan1"
            pis.append({"address": pi.strip(), "notes": notes.strip(), "wlan": wlan.strip()})
        if len(pis) == 0:
            print("Must include at least one computer!")
            sys.exit(-1)
        config['pis'] = pis
        config['lfserver'] = input(
            'Enter lf address (default: lf.internalpositioning.com): ')
        if len(config['lfserver']) == 0:
            config['lfserver'] = 'https://lf.internalpositioning.com'
        if 'http' not in config['lfserver']:
            config['lfserver'] = "http://" + config['lfserver']
        config['group'] = input('Enter a group: ')
        if len(config['group']) == 0:
            config['group'] = 'default'
        config['scantime'] = input('Enter a scanning time (default 10 seconds): ')
        if len(config['scantime']) == 0:
            config['scantime'] = 10
        try:
            config['scantime'] = int(config['scantime'])
        except:
            config['scantime'] = 10

        with open(args.config, 'w') as f:
            f.write(json.dumps(config, indent=2))

    config = json.load(open(args.config, 'r'))
    if args.group != "":
        config['group'] = args.group
        with open(args.config, 'w') as f:
            f.write(json.dumps(config, indent=2))

    config['user'] = args.user
    config['location'] = args.location
    main(args, config)