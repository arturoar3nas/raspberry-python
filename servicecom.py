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
import urllib
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


set_proctitle(b'servicecom.py')

# create logger with 'spam_application'
logger = logging.getLogger('/home/pi/servicecom/servicecom.py')
logger.setLevel(logging.DEBUG)

# change this value based on which GPIO port the relay is connected to
# for modem managed
PWR_PIN = 5


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
                sys.stderr.write(message.format(self.pidfile))
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
        os.system("sudo /usr/bin/modem3g/sakis3g disconnect")  # stop the 3G
        m = Modem()
        m.stop()
        del m
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
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
        conf = Config.getInstance()
        err_com = 0
        timeout = conf.data["ScanTime"]
        logger.info("Time Scan %d" % timeout)
        modem = Modem()
        com = ThrdGnrt()
        wd = Wacthdogapp()
        sysinfo = Sysinfo()
        com.start()  # start communication
        # wifi = Wifi()
        configmonitor = File('/home/pi/servicecom/config.json')
        while True:
            time.sleep(timeout)

            if conf.data["Flags"]["3G"] == 1:
                logger.info("check the 3g connection")
                # Then we check the 3g connection
                status_3g = com.testconnection()

                # Fail communication
                if not status_3g:
                    err_com += 1
                    logger.info("Try connections %d" % err_com)
                    if err_com > 5:
                        logger.info("Fail communication")
                        com.stop()
                        sleep(1)
                        modem.stop()
                        sleep(5)  # wait a 5 seconds and...
                        modem.start()
                        sleep(1)
                        com.start()
                        err_com = 0

            if conf.data["StopScan"] == 0:
                logger.info("check if the app still running")
                # the next stuff by do is check if the app still running
                app = wd.getstatusapp()

                # if the app is stop
                if not app:
                    logger.info("app is stop")
                    wd.startapp()

            logger.info("checked the system and put this info in the log")
            # Finally checked the system and put this info in the log
            sysinfo.getsysinfo()

            # if wi-fi flag it's enabled
            # if conf.data["Flags"]["Wifi"] == 1:
            #     # check connection wi-fi
            #     status_wifi = wifi.testConnection()
            #     if not status_wifi & conf.statuswifi:
            #         wifi.reconnect()
            #
            #     if not status_wifi:
            #         # if not connect then disconnect and connect the interface
            #         wifi.disconnect()
            #         sleep(2)
            #         wifi.reconnect()
            # # else wifi flag it's disabled disconnect the wlan0 interface
            # else:
            #     # Check to not disable all time
            #     if conf.statuswifi:
            #         wifi.disconnect()

            logger.info("veryfy json")
            if configmonitor.verify():
                conf.load()
                timeout = conf.data["ScanTime"]
                logger.info("Time Scan %d" % timeout)
                # in case the flies
                # if conf.data["Flags"]["Wifi"] == 1:
                #   wifi.verify()


class Modem:
    """
    Brief:
    The Modem SIM5320A work using the pins GPIO5 for the power
    This class managed the modem and do the follow actions:

    Usage: subclass the Daemon class and override the run() method
    1) Start:
        Turn on modem
    2) Stop:
        Turn down the modem

    """

    def __init__(self):
        # Define like output the pin
        self.pwr = gpiozero.OutputDevice(PWR_PIN, active_high=True, initial_value=True)
        return

    def start(self):
        self.pwr.on()
        sleep(0.1)  # wait a ms
        self.pwr.off()
        sleep(0.1)
        self.pwr.on()
        logger.info("Start modem...")
        return

    def stop(self):
        self.pwr.off()
        sleep(1)  # wait a s
        self.pwr.on()
        sleep(1)
        self.pwr.off()
        logger.info("Off modem...")
        return


class ThrdGnrt:
    """
    Brief:
     3G communication managed
    Usage:
        1) do ping to www.google.cl
        2) ask to modem the status
        both return a bool if the connection it's ok
    """

    def __init__(self):
        if self.testconnection():
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

    def testconnection(self):
        # logger.info("check ping!")
        # fping = self.ping()
        logger.info("check status modem")
        mstatus = self.modemstatus()
        if mstatus:
            return True
        else:
            return False

    @staticmethod
    def modemstatus():

        mystr = b'connected'
        proc = b''
        try:
            proc = subprocess.check_output(["sudo /usr/bin/modem3g/sakis3g --console status"], shell=True)  # stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        except subprocess.CalledProcessError as e:
            print(e.output)

        if proc.find(mystr) > 0:
            logger.info("Modem ok status")
            return True
        else:
            logger.info("Modem fail status")
            return False

    @staticmethod
    def ping():
        err = 0
        for i in range(1, 10):  # try 10 time
            response = os.system("ping -c 1 -i 0.2 www.google.cl")
            if response == 0:
                logger.debug("ping ok!")
            else:
                logger.error("ping fail")
                err = err + 1
        if err > 5:
            logger.info("ping fail!")
            return False
        else:
            logger.info("ping ok!")
            return True


class Wacthdogapp:
    """
    Brief: This class monitoring a app declared at config.json

    Usage:
        getstatusapp: this method check if the app is runing and return True if it's ok!
    """

    def __init__(self):
        self.conf = Config.getInstance()
        self.proc_path_name = self.conf.data["Aplication"]
        self.proc_name = os.path.basename(self.proc_path_name)

        return

    def getstatusapp(self):
        # Ask by the process
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
        subprocess.Popen("sudo python3 /%s" % self.proc_path_name, shell=True)
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
        # Get disk info
        self.disk = psutil.disk_usage('/')
        # Get cpu info
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
        fjson = open("/home/pi/servicecom/sysinfo.json", "w+")
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

    def load(self):
        # Load data from config.json
        try:
            with open('/home/pi/servicecom/config.json') as f:
                self.data = json.load(f)
        except IOError as e:
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
        except ValueError:
            print("Could not convert data to an integer.")
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise
        logger.info("Load done!")
        return

    def set3gstatus(self, status):
        self.status3g = status
        return

    def setwifistatus(self, status):
        self.statuswifi = status
        return

    @staticmethod
    def getInstance():
        """ Static access method. """
        if Config.__instance == None:
            Config()
        return Config.__instance

    def __init__(self, data):
        """ Virtually private constructor. """
        self.data = data
        self.status3g = False
        self.statuswifi = False
        if Config.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Config.__instance = self


class File:
    """
    Brief:

    Usage:

    """

    def __init__(self, file):
        self._cached_stamp = 0
        self.file = file

    def verify(self):
        stamp = os.stat(self.file).st_mtime
        if stamp != self._cached_stamp:
            self._cached_stamp = stamp
            logger.info("Has a file change")
            return True
        else:
            logger.info("No change file")
            return False

    @staticmethod
    def parsefilecmp(self, file, str1):
        with open(file, 'r') as file1:
            same = set(file1).intersection(str1)

        if same:
            return True
        else:
            return False


class Wifi:
    """
    Brief: This class managed wi-fi connection

    Usage:
        create: overwrite wpa_supplicant.conf file for store the ssid and password
        disconnect: disconnect the wlan0 interface
        reconnect: connect the wlan0 interface
        testConnection: make sure is ok the connection
        Note: after the use connect you must be will reboot the raspberry
    """

    def __init__(self):
        conf = Config.getInstance()
        self.password = conf.data["Wifi"]["Psw"]
        self.ssid = conf.data["Wifi"]["SSID"]
        return

    def create(self):
        os.system(
            "echo '\nnetwork={\n    ssid=\"" + self.ssid + "\"\n    psk=\"" + self.password + "\"\n}' | sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf")
        os.system("wpa_cli -i wlan0 reconfigure")
        return

    def disconnect(self):
        os.system("sudo ifconfig wlan0 down")
        return

    def reconnect(self):
        os.system("sudo ifconfig wlan0 up")
        return

    def testConnection(self):
        try:
            url = "https://www.google.com"
            urllib.urlopen(url)
            status = "Wi-Fi Connected"
        except:
            status = "Wi-Fi not connected"
        logger.error(status)
        if status == "Connected":
            return True
        else:
            return False

    def verify(self):
        wpa_supplicant = '/etc/wpa_supplicant/wpa_supplicant.conf'
        s = Config.getInstance()
        # check if the wpa_supplicant network object exist
        cmpssid = File.parsefilecmp(wpa_supplicant, "    ssid\"" + s.data["Wifi"]["SSID"] + "\"")
        cmpsw = File.parsefilecmp(wpa_supplicant, "    psk=\"" + s.data["Wifi"]["Psw"] + "\"")
        if not cmpssid or cmpsw:
            # if network no exist then use connect
            self.create()


if __name__ == "__main__":

    with open('/home/pi/servicecom/config.json') as f:
        data = json.load(f)
    s = Config(data)

    # create file handler which logs even debug messages
    fh = logging.FileHandler('/tmp/servicecom.log')
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
    logger.debug(json.dumps(s.data))

    daemon = MyDaemon('/home/pi/servicecom/servicecom.pid')
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
