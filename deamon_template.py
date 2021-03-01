#!/usr/bin/env python3
# coding: utf-8
""" Useful daemon template               """
""" Print the date time every one second """

import threading, time
import signal
import sys


def print_every_n_seconds(n=2):
    while True:
        print(time.ctime())
        time.sleep(n)

def signal_handler(sig, frame):
    print('Stoping program')
    sys.exit(0)

def main():
    thread = threading.Thread(target=print_every_n_seconds, daemon=True)
    thread.start()
    
    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C')
    signal.pause()

if __name__ == '__main__':
    main()
