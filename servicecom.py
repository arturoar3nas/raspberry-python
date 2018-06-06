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

import os
import gpiozero
from time import sleep
import psutil
import logging
import json
import sys
import time
import atexit
import signal
import subprocess

# create logger with 'spam_application'
logger = logging.getLogger('servicecom.py')
logger.setLevel(logging.DEBUG)

# change this value based on which GPIO port the relay is connected to
# for modem managed
PWR_PIN = 18
RST_PIN = 17


class Daemon:
    """A generic daemon class.

    Usage: subclass the daemon class and override the run() method."""

    def __init__(self, pidfile):
        self.pidfile = pidfile

    def daemonize(self):
        """Deamonize class. UNIX double fork mechanism."""

        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #1 failed: {0}\n'.format(err))
            sys.exit(1)

        # decouple from parent environment
        os.chdir('/')
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #2 failed: {0}\n'.format(err))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)

        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as f:
            f.write(pid + '\n')

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """Start the daemon."""

        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile, 'r') as pf:

                pid = int(pf.read().strip())
        except (IOError, ValueError):
            pid = None

        if pid:
            check = self.check_pid(pid)
            if check:
                message = "pidfile {0} already exist. " + \
                          "Daemon already running?\n"
                sys.stderr.write(message.formsat(self.pidfile))
                sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """Stop the daemon."""

        # Get the pid from the pidfile
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
                logger.debug("pid: %d" % pid)
        except IOError:
            pid = None

        if not pid:
            message = "pidfile {0} does not exist. " + \
                      "Daemon not running?\n"
            sys.stderr.write(message.format(self.pidfile))
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
                os.system("sudo /usr/bin/modem3g/sakis3g disconnect")  # stop the 3G
        except OSError as err:
            e = str(err.args)
            if e.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(str(err.args))
                sys.exit(1)

    def restart(self):
        """Restart the daemon."""
        self.stop()
        self.start()

    def run(self):
        """You should override this method whit you subclass Daemon.

        It will be called after the process has been daemonized by
        start() or restart()."""

    @staticmethod
    def check_pid(pid):
        """ Check For the existence of a unix pid. """
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True


class MyDaemon(Daemon):

    """override method subclass Daemon."""
    def run(self):
        modem = Modem()
        com = ThrdGnrt()
        wd = Wacthdogapp()
        sysinfo = Sysinfo()
        com.start()  # start communication
        while True:
            time.sleep(5)

            # Then we check the 3g connection
            status_3g = com.getstatus()

            # Fail communication
            if not status_3g:
                modem.stop()
                com.stop()
                sleep(2)  # wait a 2 seconds and...
                modem.start()
                com.start()

            # the next stuff by do is check if the app still running
            app = wd.getstatusapp()

            # if the app is stop
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
        self.pwr = gpiozero.OutputDevice(PWR_PIN, active_high=False, initial_value=False)
        self.rst = gpiozero.OutputDevice(RST_PIN, active_high=False, initial_value=False)
        return

    def start(self):
        self.pwr.on()
        sleep(1)  # wait a ms
        self.rst.on()
        sleep(1)  # wait a ms
        self.rst.off()
        sleep(1)  # wait a ms
        self.rst.on()
        logger.info("Start modem...")
        return

    def stop(self):
        self.pwr.on()
        sleep(1)  # wait a ms
        self.rst.on()
        sleep(1)  # wait a ms
        self.rst.off()
        sleep(1)  # wait a ms
        self.rst.on()
        logger.info("Off modem...")
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
        logger.info("Reset modem...")
        return


class ThrdGnrt:
    """
    Brief:
     3G communication managed
    Usage:

    """
    def __init__(self):
        self.start()
        return

    def start(self):
        subprocess.run("sudo /usr/bin/modem3g/sakis3g \
        connect --console --interactive \
        APN=CUSTOM_APN \
        CUSTOM_APN='imovil.entelpcs.cl' \
        APN_USER='entelcps' \
        APN_PASS='entelcps' \
        USBINTERFACE=3 \
        USBMODEM=05c6:9000 \
        OTHER=USBMODEM \
        MODEM=OTHER", shell=True)
        logger.info("Sucess Modem 3g")
        return

    def stop(self):
        os.system("sudo /usr/bin/modem3g/sakis3g disconnect")
        return

    def getstatus(self):
        fping = self.ping()
        if not fping:
            return False
        else:
            return True

    def modemstatus(self):
        """"
            Me falta Probarlo
        """
        proc = os.subprocess.Popen(["sudo", "/usr/bin/modem3g/sakis3g status"], stdout=os.subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        if out == "SIMCOM_SIM5320A connected to entel (73001).":
            return True
        else:
            return False

    def ping(self):
        err = 0
        for i in range(1, 10):  # try 10 time
            response = os.system("ping -c 1 www.google.cl")
            if response == 0:
                logger.debug("ping ok!")
            else:
                logger.error("ping fail")
                err = err + 1
        if err > 5:
            return False
        else:
            return True

class Wacthdogapp:
    """
    Brief: This class monitoring a app declared at config.json

    Usage:
        getstatusapp: this method check if the app is runing and return True if it's ok!
    """

    def __init__(self):
        self.proc_name = None
        return

    def getstatusapp(self):

        # Read the config
        conf = Config.getInstance()

        # Ask by the process
        self.proc_name = conf.data["Aplication"]
        for proc in psutil.process_iter():
            pid = psutil.Process(proc.pid)  # Get the process info using PID
            pname = proc.name()  # Here is the process name

            if pname == self.proc_name:
                logger.info("Process ok!")
                logger.info(pid)
                return True

        # if not appear the process
        logger.error("Process shut down")
        return False

    def startapp(self):
        os.system("sudo python3 ./%s" % self.proc_name)
        return


class Sysinfo:
    """
    Brief: Get the system information

    Usage: this class use psutil module for get info from the system
            too create a json file whit the data
    """
    def __init__(self):
        self.mem = None
        self.disk = None
        self.cpu = None
        self.str = ""
        return

    def getsysinfo(self):
        self.mem = psutil.virtual_memory()
        #Get disk info
        self.disk = psutil.disk_usage('/')
        #Get cpu info
        self.cpu = psutil.cpu_percent()

        self.createjson()
        return

    def createjson(self):
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
        return

    def writejson(self):
        fjson = open("/home/pi/sysinfo.json", "w+")
        fjson.write(self.str)
        fjson.close()
        return


class Config:
    """
    Brief:
        Singleton Class.
    Usage:
        for data persistence storaged at config.json
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
    formatter = logging.Formatter('%(asctime)s - %(funcName)s:%(lineno)d - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.info(json.dumps(s.data))

    daemon = MyDaemon('/home/pi/servicecom.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)

