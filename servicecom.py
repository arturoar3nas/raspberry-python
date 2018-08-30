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
from __future__ import generators

import stat
from time import sleep
import abc
import os
import sys

if sys.platform == 'linux2' or sys.platform == 'linux':
    import gpiozero
import psutil
import logging
import json
import time
import atexit
import signal
import subprocess
import ctypes
import serial
import re

# Directory
path = dict()
path['config'] = '/home/pi/servicecom/config.json'
path['log'] = '/tmp/servicecom.log'
path['pid'] = '/home/pi/servicecom/servicecom.pid'
path['pwd'] = '/home/pi/servicecom/servicecom.py'
path['wpa'] = '/etc/wpa_supplicant/wpa_supplicant.conf'
path['sys'] = "/home/pi/servicecom/sysinfo.json"
path['sim'] = '/home/pi/servicecom/simstatus.json'

# create logger with 'spam_application'
logger = logging.getLogger(path['pwd'])
logger.setLevel(logging.DEBUG)

# change this value based on which GPIO port the relay is connected to
# for modem managed
PWR_PIN = 5


def loggerhandler(pathlogger):
    # create file handler which logs even debug messages
    fh = logging.FileHandler(pathlogger)
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


class ProcName(object):
    def __init__(self):
        return

    @staticmethod
    def set(new_title):
        # Change name process
        lib = ctypes.cdll.LoadLibrary(None)
        prctl = lib.prctl
        prctl.restype = ctypes.c_int
        prctl.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_ulong,
                          ctypes.c_ulong, ctypes.c_ulong]
        result = prctl(15, new_title, 0, 0, 0)
        if result != 0:
            raise OSError("prctl result: %d" % result)


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
                logger.error(str(err.args))
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
        logger.info("Building RTU")
        builder = ConcreteBuilder()
        director = Director()
        director.setBuilder(builder)
        self.rtu = director.getProduct()
        self.rtu.specification()
        self.rtu.gprs.err = 0
        self.timeout = self.rtu.conf.data["ScanTime"]
        logger.info("Time Scan %s" % self.timeout)

        while True:
            try:
                logger.info("wait...")
                time.sleep(int(self.timeout))
                self.GprsTask()
                self.ScanTask()
                self.SysInfoTask()
                self.WifiTask()
                self.PersistenceTask()
            except Exception as e:
                # THis will catch any exception!
                logger.error("Something terrible happened %s" % e)
                sys.exit(2)

    def GprsTask(self):

        # get the network info
        if self.rtu.conf.data["Flags"]["3g"] == "1":
            logger.info("Query at commands")
            self.rtu.at.query()

            logger.info("check the 3g connection")
            # Then we check the 3g connection
            status_3g = self.rtu.gprs.testconnection()

            # Fail communication
            if not status_3g:
                self.rtu.gprs.err += 1
                logger.info("Try connections %d" % self.rtu.gprs.err)
                if self.rtu.gprs.err > 5:
                    try:
                        logger.info("Fail communication")
                        # self.rtu.gprs.stop()
                        # sleep(1)
                        # self.rtu.modem.stop()
                        # sleep(5)  # wait a 5 seconds and...
                        self.rtu.modem.start()
                        sleep(5)
                        self.rtu.gprs.start()
                        self.rtu.gprs.err = 0
                    except Exception as e:
                        logger.error("Error trying to start modem %s" % e)

    def ScanTask(self):
        if self.rtu.conf.data["StopScan"] == "0":
            logger.info("check if the app still running")
            # the next stuff by do is check if the app still running
            app, self.rtu.conf.data = self.rtu.wd.getstatusapp()
            print(json.dumps(self.rtu.conf.data))

            # if the app is stop
            if not app:
                logger.info("app is stop")
                self.rtu.wd.startapp()

    def SysInfoTask(self):
        logger.info("checked the system and put this info in the log")
        # Finally checked the system and put this info in the log
        self.rtu.sysinfo.getsysinfo()

    def WifiTask(self):
        # if wi-fi flag it's enabled
        if self.rtu.conf.data["Flags"]["Wifi"] == "1":
            # check the setting
            ssid, psw = self.rtu.wifi.verify()
            logger.info("ssid = %r  psw = %r" % (ssid, psw))
            if ssid is False or psw is False:
                self.rtu.wifi.network_props(self.rtu.conf)

            # check connection wi-fi
            status_wifi = self.rtu.wifi.test_connection()
            if not status_wifi:
                # if not connect then disconnect and connect the interface
                self.rtu.wifi.disconnect()
                time.sleep(3)
                self.rtu.wifi.reconnect()

    def PersistenceTask(self):
        logger.info("veryfy json")
        if self.rtu.configmonitor.verify():
            oldWifi = self.rtu.conf.data["Flags"]["Wifi"]
            oldGprs = self.rtu.conf.data["Flags"]["3g"]
            self.rtu.conf.load()
            self.timeout = self.rtu.conf.data["ScanTime"]
            logger.info("Time Scan %s" % self.timeout)
            logger.info(json.dumps(self.rtu.conf.data))

            if self.rtu.conf.data["Flags"]["Wifi"] == "0" \
                    and oldWifi != self.rtu.conf.data["Flags"]["Wifi"]:
                self.rtu.wifi.disconnect()

            if self.rtu.conf.data["Flags"]["3g"] == "0" \
                and oldGprs != self.rtu.conf.data["Flags"]["3g"]:
                self.rtu.gprs.stop()
                sleep(1)
                self.rtu.modem.stop()


class Modem(object):
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
        logger.info("Create Modem")
        self.pwr = gpiozero.OutputDevice(PWR_PIN, active_high=True, initial_value=True)
        return

    def start(self):
        try:
            logger.info("Starting Modem...")
            self.pwr.on()
            sleep(0.1)  # wait a ms
            self.pwr.off()
            sleep(0.1)
            self.pwr.on()
            logger.info("Start modem...")
        except Exception:
            logger.error("unexpected error stating Modem GPIO")

        return

    def stop(self):
        try:
            logger.info("Stoping Modem....")
            self.pwr.off()
            sleep(1)  # wait a s
            self.pwr.on()
            sleep(1)
            self.pwr.off()
            logger.info("Off modem...")
        except Exception:
            logger.error("unexpected error stoping Modem GPIO")
        return


class GPRS(metaclass=abc.ABCMeta):
    """
    Brief:
     3G communication managed
    Usage:
        1) do ping to www.google.cl
        2) ask to modem the status
        both return a bool if the connection it's ok
    This class use ttyUSB3
    """

    def __init__(self):
        self.data = None
        self.err = 0
        return

    def factory(type):
        if type == 'sasky':
            return Sasky3G()
        assert 0, "Bad shape creation: " + type

    factory = staticmethod(factory)

    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass

    @abc.abstractmethod
    def testconnection(self):
        pass

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


class Sasky3G(GPRS):
    """
    Brief:
     3G communication managed
    Usage:
        1) do ping to www.google.cl
        2) ask to modem the status
        both return a bool if the connection it's ok
    This class use ttyUSB3
    """

    def start(self):
        try:
            logger.info("Starting 3g com")
            myconf = Config.getInstance()
            apn = myconf.data["3G"]["Apn"]
            psw = myconf.data["3G"]["Psw"]
            usr = myconf.data["3G"]["User"]

            subprocess.run("sudo /usr/bin/modem3g/sakis3g \
            connect --console --interactive \
            APN=CUSTOM_APN \
            CUSTOM_APN='" + apn + "' \
            APN_USER='" + usr + "' \
            APN_PASS='" + psw + "' \
            USBINTERFACE=3 \
            USBMODEM=05c6:9000 \
            OTHER=USBMODEM \
            MODEM=OTHER", timeout=30, shell=True)  #
            logger.info("Sucess Modem 3g")
        except subprocess.CalledProcessError as e:
            logger.error("Error starting Modem")
            logger.error(e)
        except Exception:
            logger.error("Unexpected error... starting 3g comunnication")
        return

    def stop(self):
        logger.info("Stoping 3g Com")
        try:
            os.system("sudo /usr/bin/modem3g/sakis3g disconnect")
        except OSError:
            logger.error("Unexpected error... stoping 3g communication")
        return

    def testconnection(self):
        # logger.info("check ping!")
        # fping = self.ping()
        logger.info("Testing modem")
        mstatus = self.modemstatus()
        if mstatus:
            return True
        else:
            return False

    @staticmethod
    def modemstatus():
        logger.info("Getting status from 3g com...")
        mystr = b'connected'
        proc = b''
        try:
            proc = subprocess.check_output(["sudo /usr/bin/modem3g/sakis3g --console status"],
                                           shell=True)  # stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        except subprocess.CalledProcessError as e:
            logger.error(e.output)

        if proc.find(mystr) > 0:
            logger.info("Modem ok status")
            return True
        else:
            logger.info("Modem fail status")
            return False


class Wacthdogapp(object):
    """
    Brief: This class monitoring a app declared at config.json

    Usage:
        getstatusapp: this method check if the app is runing and return True if it's ok!
    """

    def __init__(self):
        logger.info("Create wathch dog")
        self.conf = Config.getInstance()
        self.proc_path_name = self.conf.data["Aplication"]
        self.proc_name = os.path.basename(self.proc_path_name)

        return

    def getstatusapp(self):
        # Ask by the process
        try:
            for proc in psutil.process_iter():
                pid = psutil.Process(proc.pid)  # Get the process info using PID
                pname = proc.name()  # Here is the process name

                if pname == self.proc_name:
                    logger.info("Process ok!")
                    self.conf.data['StatusApp'] = 'Proceso Ok'
                    logger.info(pid)
                    self.savejson()
                    return True, self.conf.data

            # if not appear the process
            logger.error("Process shut down")
            self.conf.data['StatusApp'] = 'Proceso suspendido'
            self.savejson()
        except Exception as e:
            # THis will catch any exception!
            logger.error("Something terrible happened %s" % e)
        return False, self.conf.data

    def startapp(self):
        logger.info("Starting WolkeCounter")
        os.system("sudo python3 %s &" % self.proc_path_name)
        return

    def savejson(self):
        # try:
        #     fjson = open(path['config'], "w+")
        #     data = json.load(fjson)
        #     data['StatusApp'] = self.conf.data['StatusApp']
        #     fjson.write(json.dumps(data, indent=4, sort_keys=True))
        #     fjson.close()
        # except IOError as e:
        #     logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))
        # except ValueError:
        #     logger.error("Could not convert data to an integer.")
        # except:
        #     logger.error("Unexpected error:", sys.exc_info()[0])
        #     raise
        return


class Sysinfo(object):
    """
    Brief: Get the system information

    Usage: this class use psutil module for get info from the system
            too create a json file whit the data
    """

    def __init__(self):
        logger.info("Create sys info")
        self.mem = None
        self.disk = None
        self.cpu = None
        self.str = ""
        return

    def getsysinfo(self):
        logger.info("getting sys info")
        self.mem = psutil.virtual_memory()
        # Get disk info
        self.disk = psutil.disk_usage('/')
        # Get cpu info
        self.cpu = psutil.cpu_percent()

        self.createjson()
        return

    def createjson(self):
        data["ActiveMemory"] = self.mem.active
        data["AvailableMemory"] = self.mem.available
        data["BufferMemory"] = self.mem.buffers
        data["CachedMemory"] = self.mem.cached
        data["FreeMemory"] = self.mem.free
        data["InactiveMemory"] = self.mem.inactive
        data["TotalMemory"] = self.mem.total
        data['Diskfree'] = self.disk.free
        data['Diskused'] = self.disk.used
        data['Disktotal'] = self.disk.total
        data['CpuPercent'] = self.cpu
        self.str = json.dumps(data)
        self.writejson()
        return

    def writejson(self):
        fjson = open(path['sys'], "w+")
        fjson.write(self.str)
        fjson.close()
        return


class Config(object):
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
            with open(path['config']) as f:
                self.data = json.load(f)
        except IOError as e:
            logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))
        except ValueError:
            logger.error("Could not convert data to an integer.")
        except:
            logger.error("Unexpected error:", sys.exc_info()[0])
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
        logger.info("Creating singleton")
        """ Virtually private constructor. """
        self.data = data
        self.status3g = False
        self.statuswifi = False
        if Config.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Config.__instance = self


class File(object):
    """
    Brief:

    Usage:

    """

    def __init__(self, file):
        logger.info("Create file object")
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
    def parsefilecmp(file, str1):
        logger.info("file: %s" % file)
        logger.info("strl: %s" % str1)
        try:
            with open(file, 'rt') as file1:
                read_data = file1.read()
                if str1 in read_data:
                    logger.debug("read_data: %s" % read_data)
                    return True
        except IOError:
            logger.error("Can't open file %s" % file)

        return False

    def rplcinfile(self, file, oldstr1, str):
        logger.info("file: %s" % file)
        logger.info("strl: %s" % str)
        if not oldstr1:
            return False
        oldstr1 = oldstr1.replace(' ', '')
        try:
            with open(file, 'r+') as file1:
                read_data = file1.read()
                logger.info("read_data: %s \n" % read_data)
                file1.close()
                lines = read_data.split('\n')
                logger.info("str %s" % str)
                logger.info("old str %s" % oldstr1)
                for line in lines:
                    logger.info("line %s" % line)
                    if line in oldstr1:
                        data = read_data.replace(oldstr1, str)
                        with open(file, "w") as f:
                            logger.info("data: %s\n" % data)
                            f.write(data)
                            f.close()
                        return True

        except IOError:
            logger.error("Can't open file %s" % file)
            sys.exit(2);
        return False


class Wifi(object):
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
        self.password = None
        self.ssid = None
        self.oldssid = None
        self.oldpassword = None
        return

    def getsetup(self):
        try:
            with open(path['wpa'], 'rt') as file1:
                read_data = file1.read()
                lines = read_data.split('\n')
                for line in lines:
                    if 'psk' in line:
                        str = line.replace('psk=', '').replace('"', '')
                        self.oldpassword = str
                        logger.info(self.oldpassword)
                    if 'ssid' in line:
                        str = line.replace('ssid=', '').replace('"', '')
                        self.oldssid = str
                        logger.info(self.oldssid)
                return True
        except IOError:
            logger.error("Can't open file ")
            sys.exit(2)

        return False

    def network_props(self, conf):
        try:
            self.password = conf.data["Wifi"]["Psw"]
            self.ssid = conf.data["Wifi"]["Ssid"]

            # if exist the temporary file
            self.getsetup()
            file = File(path['wpa'])
            retpsw = file.rplcinfile(path['wpa'], self.oldpassword, self.password)
            retssid = file.rplcinfile(path['wpa'], self.oldssid, self.ssid)
            if retpsw and retssid is False:
                #  then we set the config
                os.system(
                    "echo '\nnetwork={\n    ssid=\"" + self.ssid + "\"\n    psk=\"" + self.password + "\"\n}' \
                    | sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf")

            logger.info("Reconfigure supplicant wlan0")
            os.system("wpa_cli -i wlan0 reconfigure")
            logger.info("done! wlan0")
        except IOError as e:
            logger.error("Error writing wpa_supplicant.conf")
            logger.error(e)
        except OSError as e:
            logger.error("OS Error setting wpa_supplicant")
            logger.error(e)

        return

    @staticmethod
    def disconnect():
        os.system("sudo ifconfig wlan0 down")
        logger.info("disconect ifconfig wlan0 down")
        return

    @staticmethod
    def reconnect():
        os.system("sudo ifconfig wlan0 up")
        logger.info("reconect ifconfig wlan0 up")
        return

    @staticmethod
    def test_connection():
        err = 0
        try:
            for i in range(1, 10):  # try 10 time
                response = os.system("ping -c 1 -i 0.2 www.google.cl")
                if response == 0:
                    logger.debug("ping ok!")
                else:
                    logger.error("ping fail")
                    err = err + 1
        except Exception as e:
            logger.error("Can't do ping!")
            logger.error(e)
            return False

        if err > 5:
            logger.info("ping fail!")
            return False
        else:
            logger.info("ping ok!")
            return True

    @staticmethod
    def verify():
        try:
            wpa_supplicant = path['wpa']
            conf = Config.getInstance()

            # check if the wpa_supplicant network object exist
            ssid = File.parsefilecmp(wpa_supplicant, "    ssid=\"" + conf.data["Wifi"]["Ssid"] + "\"")
            psw = File.parsefilecmp(wpa_supplicant, "    psk=\"" + conf.data["Wifi"]["Psw"] + "\"")

        except Exception as e:
            logger.error("Can't verify wifi settings %s" % e)

        return ssid, psw


class LoadingBar(object):
    """
    Brief: This class create a load bar in command prompt

    Usage:
        just invoke start method and pass a integer with the seconds to wait
    """

    def __init__(self):
        return

    @staticmethod
    def start(seconds):
        for i in range(0, seconds):
            percent = float(i) / seconds
            hashes = '#' * int(round(percent * seconds))
            spaces = ' ' * (seconds - len(hashes))
            logger.info("\rStarting Daemon Percent: [{0}] {1}%".format(hashes + spaces, int(round(percent * 100))))
            time.sleep(1)


class AtCommand(object):
    """
    Brief: This class managed use cmd AT for talk with the modem

    Usage:
        query: get info about rssi, IMEI, network type, network status,
        roaming status and about the apn
        If you need try a new AT cmd use this line:
        # sudo chat -V -s '' 'AT+CIPSTART=?' 'OK' '' > /dev/ttyUSB2 < /dev/ttyUSB2
        This class use ttyUSB2
    """

    def __init__(self):
        self.rssi_dict = dict()
        self.rssi_dict['2'] = '-109'
        self.rssi_dict['3'] = '-107'
        self.rssi_dict['4'] = '-105'
        self.rssi_dict['5'] = '-103'
        self.rssi_dict['6'] = '-101'
        self.rssi_dict['7'] = '-99'
        self.rssi_dict['8'] = '-97'
        self.rssi_dict['9'] = '-95'
        self.rssi_dict['10'] = '-93'
        self.rssi_dict['11'] = '-91'
        self.rssi_dict['12'] = '-89'
        self.rssi_dict['13'] = '-87'
        self.rssi_dict['14'] = '-85'
        self.rssi_dict['15'] = '-83'
        self.rssi_dict['16'] = '-81'
        self.rssi_dict['17'] = '-79'
        self.rssi_dict['18'] = '-77'
        self.rssi_dict['19'] = '-75'
        self.rssi_dict['20'] = '-73'
        self.rssi_dict['21'] = '-71'
        self.rssi_dict['22'] = '-69'
        self.rssi_dict['23'] = '-67'
        self.rssi_dict['24'] = '-65'
        self.rssi_dict['25'] = '-63'
        self.rssi_dict['26'] = '-61'
        self.rssi_dict['27'] = '-59'
        self.rssi_dict['28'] = '-57'
        self.rssi_dict['29'] = '-55'
        self.rssi_dict['30'] = '-53'

        self.status_dict = dict()
        self.status_dict['0'] = 'Registrado'
        self.status_dict['1'] = 'Registrado'
        self.status_dict['2'] = 'No registrado, buscando operador'
        self.status_dict['3'] = 'Registro negado'
        self.status_dict['4'] = 'Desconocido'
        self.status_dict['5'] = 'Registrado, roaming'
        self.status_dict['6'] = 'Registrado, solo SMS'
        self.status_dict['7'] = 'Registrado solo SMS, roaming'
        self.status_dict['8'] = 'Solo servicios de Emergencia'
        self.status_dict['9'] = 'Registrado "CSFB no privilegiado"'
        self.status_dict['10'] = 'Registrado "CSFB no privilegiado", roaming'

        self.type_dict = dict()
        self.type_dict['12'] = 'GSM EDGE'
        self.type_dict['22'] = '3G'
        self.type_dict['25'] = 'GSM EDGE/3G/LTE'
        self.type_dict['28'] = 'LTE'
        self.type_dict['29'] = 'GSM/3G'
        self.type_dict['30'] = 'GSM/LTE'
        self.type_dict['31'] = '3G/LTE'

        self.ser = None
        self.data = dict()
        self.status = False
        self.port = dict()
        self.port[0] = '/dev/ttyUSB0'
        self.port[1] = '/dev/ttyUSB1'
        self.port[2] = '/dev/ttyUSB2'
        self.port[3] = '/dev/ttyUSB3'
        self.port[4] = '/dev/ttyUSB4'
        self.port[5] = '/dev/ttyUSB5'
        self.port[6] = '/dev/ttyUSB6'
        return

    def getStatus(self):
        return self.status



    def getrssi(self):
        logger.info("get RSSI")
        try:
            lines = self.sendcomd(b'AT+CSQ\r')[1]
        except:
            logger.error("Cant get Rssi data!")
            return

        if '+CSQ' in lines:
            try:
                index = lines.replace('\r', '').replace('+CSQ:', '').replace(' ', '').split(',')[0]
                self.data['Signal'] = self.rssi_dict[index]
            except ValueError:
                logger.error("Could not convert data to an integer.")
            except IndexError:
                logger.error("Index error...")
            except:
                logger.error("Unexpected error:", sys.exc_info()[0])
        return

    def getImei(self):
        logger.info("get IMEI")
        try:
            lines = self.sendcomd(b'AT+CGSN\r')
        except:
            logger.error("Cant get IMEI data!")
            return

        for i, line in enumerate(lines):
            if i == 1:
                try:
                    self.data['Imei'] = line.replace('\r', '')
                except ValueError:
                    logger.error("Could not convert data to an integer.")
                except:
                    logger.error("Unexpected error:", sys.exc_info()[0])
        return

    def gettype(self):
        logger.info("get TYPE")
        try:
            line = self.sendcomd(b'AT+WS46?\r')[1]
        except:
            logger.error("Cant get TYPE data!")
            return
        try:
            index = line.replace('\r', '').replace(' ', '').split(',')[0]
            self.data['Type'] = self.type_dict[index]
        except ValueError:
            logger.error("Could not convert data to an integer.")
        except:
            logger.error("Unexpected error:", sys.exc_info()[0])
        return

    def getstatus(self):
        try:
            logger.info("get STATUS")
            line = self.sendcomd(b'AT+CREG?\r')[1]
        except:
            logger.error("Cant get STATUS data!")
            return
        if '+CREG:' in line:
            try:
                str = line.replace('\r', '').replace('+CREG:', '').replace(' ', '').split(',')
                self.data['Status'] = self.status_dict[str[0]]
            except ValueError:
                logger.error("Could not convert data to an integer.")
            except:
                logger.error("Unexpected error:", sys.exc_info()[0])
        return

    def getroaming(self):
        logger.info("get ROAMING")
        try:
            line = self.sendcomd(b'AT+CREG?\r')[1]
        except:
            logger.error("Cant get ROAMING data!")
            return
        if '+CREG:' in line:
            try:
                str = line.replace('\r', '').replace('+CREG:', '').replace(' ', '').split(',')
                if str[0] == '5' or str[0] == '7' or str[0] == '10':
                    self.datap['Roaming'] = 'Habilitado'
                else:
                    self.data['Roaming'] = 'Deshabilitado'
            except ValueError:
                logger.error("Could not convert data to an integer.")
            except:
                logger.error("Unexpected error:", sys.exc_info()[0])
        return

    def getnetwork(self):
        logger.info("get NETWORK")
        try:
            lines = self.sendcomd(b'AT+COPS?\r')
        except:
            logger.error("Cant get NETWORK data!")
            return
        for line in lines:
            if '+COPS' in line:
                try:
                    str = line.replace('\r', '').replace('+COPS:', '')
                    list = re.findall(r'"([^"]*)"', str)
                    for l in list:
                        self.data['Red'] = l
                except ValueError:
                    logger.error("Could not convert data to an integer.")
                except:
                    logger.error("Unexpected error:", sys.exc_info()[0])
        return

    def query(self):
        if self.opentty():
            self.load()
            self.getImei()
            self.getrssi()
            self.getstatus()
            self.gettype()
            self.getroaming()
            self.getnetwork()
            self.savejson()
        return

    @staticmethod
    def disk_exists(path):
        try:
            pc1 = subprocess.Popen('find '+ path, stdout=subprocess.PIPE, shell=True)
            if pc1 == path:
                logger.info(pc1)
                return True
        except:
            return False

    def opentty(self):
        ret = False
        for i in range(0, 6):
            try:
                self.ser = serial.Serial(port=self.port[i], baudrate=9600, bytesize=8, parity='N', stopbits=1,
                                         timeout=1,
                                         rtscts=True, dsrdtr=True)
                ret = True
                break
            except (ValueError, TypeError, AttributeError) as e:
                logger.error(e)
                ret = False
                continue
            except:
                logger.error('Unexpected Exception Trying to open port %s' % self.port)
                ret = False
                continue

        return ret

    def sendcomd(self, cmd):
        self.ser.write(cmd)
        msg = self.ser.read(64)
        lines = msg.decode().split('\n')
        return lines

    def savejson(self):
        try:
            logger.info("Save json")
            fjson = open(path['sim'], "w+")
            fjson.write(json.dumps(self.data, indent=4, sort_keys=True))
            fjson.close()
        except IOError as e:
            logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))
        except ValueError:
            logger.error("Could not convert data to an integer.")
        except:
            logger.error("Unexpected error:", sys.exc_info()[0])
            raise
        return

    def load(self):
        try:
            logger.info("Load json")
            with open(path['sim']) as f:
                self.data = json.load(f)
                # logger.info(self.data)
                f.close()
        except IOError as e:
            logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))
        except ValueError:
            logger.error("Could not convert data to an integer.")
        except:
            logger.error("Unexpected error:", sys.exc_info()[0])
            raise
        return


class Persistence(metaclass=abc.ABCMeta):

    def __init__(self):
        self.data = None
        return

    def factory(type):
        if type == "Json":
            return PersistenceJson()
        assert 0, "Bad shape creation: " + type

    factory = staticmethod(factory)

    @abc.abstractmethod
    def load(self, path):
        pass

    @abc.abstractmethod
    def save(self, path):
        pass


class PersistenceJson(Persistence):
    """
    Brief:

    Usage:

    """

    def load(self, path):
        try:
            with open(path) as f:
                self.data = json.load(f)
                f.close()
                return self.data
        except IOError as e:
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
        except ValueError:
            print("Could not convert data to an integer.")
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise
        return

    def save(self, path):
        try:
            fjson = open(path)
            fjson.write(json.dumps(self.data, indent=4, sort_keys=True))
            fjson.close()
        except IOError as e:
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
        except ValueError:
            print("Could not convert data to an integer.")
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise
        return


class Director(object):
    """ Controls the construction process.
    Director has a builder associated with him. Director then
    delegates building of the smaller parts to the builder and
    assembles them together.
    """

    __builder = None

    def setBuilder(self, builder):
        self.__builder = builder

    # The algorithm for assembling a car
    def getProduct(self):
        rtu = RTU()

        # First goes the body
        modem = self.__builder.getModem()
        rtu.setModem(modem)

        # Then engine
        com = self.__builder.getGPRS()
        rtu.setGPRS(com)

        wifi = self.__builder.getWifi()
        rtu.setWifi(wifi)

        sysinfo = self.__builder.getSysInfo()
        rtu.setSysInfo(sysinfo)

        at = self.__builder.getAt()
        rtu.setAt(at)

        conf = self.__builder.getConf()
        rtu.setConf(conf)

        wd = self.__builder.getWd()
        rtu.setWd(wd)

        monitor = self.__builder.getConfigMonitor()
        rtu.setConfigMonitor(monitor)

        return rtu


# The whole product
class RTU(object):
    """ The final product.
    """

    def __init__(self):
        self.wifi = None
        self.gprs = None
        self.modem = None
        self.sysinfo = None
        self.at = None
        self.conf = None
        self.wd = None
        self.configmonitor = None

    def setModem(self, modem):
        self.modem = modem

    def setWifi(self, wifi):
        self.wifi = wifi

    def setGPRS(self, gprs):
        self.gprs = gprs

    def setSysInfo(self, sysinfo):
        self.sysinfo = sysinfo

    def setAt(self, at):
        self.at = at

    def setConf(self, conf):
        self.conf = conf

    def setWd(self, wd):
        self.wd = wd

    def setConfigMonitor(self, monitor):
        self.configmonitor = monitor

    def specification(self):
        logger.info("Modem: %s" % self.modem.pwr)
        logger.info("gprs: %s" % self.gprs.data)
        logger.info("Wifi: %s" % self.wifi.ssid)


class Builder(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def getWifi(self):
        pass

    @abc.abstractmethod
    def getGPRS(self):
        pass

    @abc.abstractmethod
    def getModem(self):
        pass

    @abc.abstractmethod
    def getSysInfo(self):
        pass

    @abc.abstractmethod
    def getAt(self):
        pass

    @abc.abstractmethod
    def getConf(self):
        pass

    @abc.abstractmethod
    def getWd(self):
        pass

    @abc.abstractmethod
    def getConfigMonitor(self):
        pass


class ConcreteBuilder(Builder):
    """ Concrete Builder implementation.
    """

    def getWifi(self):
        wifi = Wifi()
        return wifi

    def getGPRS(self):
        com = GPRS.factory('sasky')
        return com

    def getModem(self):
        modem = Modem()
        return modem

    def getSysInfo(self):
        sysinfo = Sysinfo()
        return sysinfo

    def getAt(self):
        at = AtCommand()
        return at

    def getConf(self):
        conf = Config.getInstance()
        return conf

    def getWd(self):
        wd = Wacthdogapp()
        return wd

    def getConfigMonitor(self):
        monitor = File(str(path['config']))
        return monitor


if __name__ == "__main__":

    if sys.platform == 'win32':
        logger.error("Platform error... No support win32")
        com = GPRS.factory('sasky')
        print(type(com))
        sys.exit(0)

    elif sys.platform == 'linux2' or sys.platform == 'linux':
        # Change process name
        ProcName.set(b'servicecom.py')
        loggerhandler(path['log'])
        try:
            with open(path['config']) as f:
                data = json.load(f)
        except IOError:
            logger.error("Can't open config.json")
            sys.exit(2)

        # load config data
        s = Config(data)

        daemon = MyDaemon(path['pid'])
        if len(sys.argv) == 2:
            if 'start' == sys.argv[1]:
                # wait 10 seconds before start daemon
                LoadingBar.start(10)
                logger.info(json.dumps(s.data))
                daemon.start()
            elif 'stop' == sys.argv[1]:
                daemon.stop()
            elif 'restart' == sys.argv[1]:
                daemon.restart()
            elif 'debug' == sys.argv[1]:
                daemon.run()
            elif 'try' == sys.argv[1]:
                wifi = Wifi()
                ssid, psw = wifi.verify()
                logger.info("ssid = %r  psw = %r" % (ssid, psw))
                if ssid is False or psw is False:
                    wifi.network_props(s)
            else:
                print("Unknown command")
                print("usage: %s start|stop|restart" % sys.argv[0])
                sys.exit(2)
            sys.exit(0)
        else:
            print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(0)
    else:
        raise Exception("Sorry: no implementation for your platform ('%s') available" % sys.platform)
        sys.exit(0)
