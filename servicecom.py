#!/usr/bin/python3

"""
# Copyright 2015-2017 Zack Scholl. All rights reserved.
# Use of this source code is governed by a AGPL
# license that can be found in the LICENSE file.
# Service to managed
#
#
#
#
"""
import sys
import os
import gpiozero
from time import sleep
import psutil
import platform
import datetime
import time
import logging
import atexit
from signal import SIGTERM
import json
import builtins

print("servicecom start")

# create logger with 'spam_application'
logger = logging.getLogger('servicecom.py')
logger.setLevel(logging.DEBUG)
logger.info("servicecom start")

# change this value based on which GPIO port the relay is connected to
# for modem managed
PWR_PIN = 18
RST_PIN = 17


class Daemon:
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
            logger.error("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as e:
            logger.error("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = builtins.file(self.stdin, 'r')
        so = builtins.file(self.stdout, 'a+')
        se = builtins.file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        builtins.file(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = builtins.file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = builtins.file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            logger.info(message % self.pidfile)
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                logger.error(str(err))
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
        modem = Modem()
        com = ThrdGnrt()
        wd = Wacthdogapp()
        sysinfo = Sysinfo()

        # First we Check the status from modem
        modem.getstatus()

        # Then we check the 3g connection
        com.getstatus()

        # the next stuff by do is check if the app still running
        app = wd.getstatusapp()

        # if the app is stoped
        if not app:
            wd.startapp()

        # Finally checked the system and put this info in the log
        sysinfo.getsysinfo()


class Modem:
    """
    Brief:
    The Modem xxxx work using the pins xx for the power and xx for the reset
    This class managed the modem and do the follow actions:

    Usage: subclass the Daemon class and override the run() method
    1) Start modem
    """
    def __init__(self):
        # Define like output the pin
        pwr = gpiozero.OutputDevice(PWR_PIN, active_high=False, initial_value=False)
        rst = gpiozero.OutputDevice(RST_PIN, active_high=False, initial_value=False)
        return

    def start(self):
        self.pwr.on()
        sleep(1)  # wait a ms
        self.rst.on()
        sleep(1)  # wait a ms
        self.rst.off()
        sleep(1)  # wait a ms
        self.rst.on()
        print("Start modem...")
        return

    def stop(self):
        self.pwr.on()
        sleep(1)  # wait a ms
        self.rst.on()
        sleep(1)  # wait a ms
        self.rst.off()
        sleep(1)  # wait a ms
        self.rst.on()
        print("Off modem...")
        return

    def getstatus(self):
        logger.info("Status modem...")
        return

    def reset(self):
        self.pwr.on()
        sleep(1)  # wait a ms
        self.rst.on()
        sleep(1)  # wait a ms
        self.rst.off()
        sleep(1)  # wait a ms
        self.rst.on()
        print("Reset modem...")
        return


class ThrdGnrt:
    """
    Brief:
     3G communication managed
    Usage:

    """
    def __init__(self):
        return

    def getstatus(self):
        return


class Wacthdogapp:
    """
    Brief:

    Usage:

    """

    def __init__(self):
        return

    def getstatusapp(self):

        # Read the config
        conf = Config.getInstance()

        # Ask by the process
        proc_name = conf.data["Aplication"]
        for proc in psutil.process_iter():
            pid = psutil.Process(proc.pid)  # Get the process info using PID
            pname = proc.name()  # Here is the process name

            if pname == proc_name:
                logger.info("Process ok!")
                logger.info(pid)
                return True

        #if not appear the process
        logger.error("Process shut down")
        return False

    def startapp(self):
        os.system("sudo service postgresql start")
        #os.system("sudo python3 ./Demo.py")
        return


class Sysinfo:
    """
    Brief:

    Usage:

    """
    def __init__(self):
        return

    def getsysinfo(self):
        # Get memory info
        self.mem = psutil.virtual_memory()
        #Get disk info
        self.disk = psutil.disk_usage('/')
        #Get cpu info
        self.cpu = psutil.cpu_percent()

        self.createjson()
        return

    def createjson(self):
        data = {}
        data["Active Memory"] = self.mem.active
        data["Available Memory"] = self.mem.available
        data["Buffer Memory"] = self.mem.buffers
        data["Cached Memory"] = self.mem.cached
        data["Free Memory"] = self.mem.free
        data["Inactive Memory"] = self.mem.inactive
        data["Total Memory"] = self.mem.total
        data['diskfree'] = self.disk.free
        data['diskused'] = self.disk.used
        data['disktotal'] = self.disk.total
        data['Cpu Percent'] = self.cpu
        self.str = json.dumps(data)
        self.writejson()

    def writejson(self):
        fjson = open("sysinfo.json", "w+")
        fjson.write(self.str)
        fjson.close()


class Config:
    """
    Brief:

    Usage:

    """
    # Here will be the instance stored.
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if Config.__instance == None:
            Config()
        return Config.__instance

    def __init__(self, data):
        """ Virtually private constructor. """
        self.data = data
        if Config.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Config.__instance = self


if __name__ == "__main__":
    with open('config.json') as f:
        data = json.load(f)
    s = Config(data)

    # create file handler which logs even debug messages
    fh = logging.FileHandler('servicecom.log')
    ch = logging.StreamHandler()
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
    srlz = json.dumps(s.data)
    logger.info(srlz)

    """
    test
    """
    wd = Wacthdogapp()
    wd.getstatusapp()
    wd.startapp()

