#!/usr/bin/python3

"""
  Service Communication Manager
  This Python Script Damon do the below stuff:
  Check the communication 3G
  Check and Control the Status modem
  Check the status application
  Check the status info and create a json file
  The Documentation of each class it's inside of them
"""

import time
import ctypes

# Change name process
lib = ctypes.cdll.LoadLibrary(None)
prctl = lib.prctl
prctl.restype = ctypes.c_int
prctl.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_ulong,
                  ctypes.c_ulong, ctypes.c_ulong]


def set_proctitle(new_title):
    result = prctl(15, new_title, 0, 0, 0)
    if result != 0:
        raise OSError("prctl result: %d" % result)


def main():
    while True:
        time.sleep(2)


if __name__ == "__main__":
    set_proctitle(b'Demo.py')
    main()
