# Servicecom
# Tutorial
## Service Communication Manager
  This Python Script Daemon do the below stuff:
  - Check the communication 3G
  - Check and Control the Status modem
  - Check the status application
  - Check the status info and create a json file
  The Documentation of each class it's inside of them
  The Daemon generetae the following files:
  - servicecom.log
  - sysinfo.json

##  Features
    You need first edit config.json and set the following items for the communication 3g
    - APN
    - user
    - password

    and will you need set the program to at config.json for monitoring with the full path.

    First of all copy the files config.json and servicecom.py to /home/pi directory

    then you will need add the time scan to daemon in the config.json

### Installation

#### Python

Servicecom requires [Python](https://www.python.org/) v3+ to run.
```sh
$ sudo apt-get install python3
$ sudo apt install python3-gpiozero
$ sudo apt install python3-psutil
```
#### Sakis3G

Servicecom requires [Sakis3G](http://raspberry-at-home.com/files/sakis3g.tar.gz).

Install the dependencies and Dependencies and start the modem.
```sh
$ sudo apt-get update
$ sudo apt-get install ppp
$ wget "http://raspberry-at-home.com/files/sakis3g.tar.gz"
$ sudo mkdir /usr/bin/modem3g
$ sudo chmod 777 /usr/bin/modem3g
$ sudo cp sakis3g.tar.gz /usr/bin/modem3g
$ cd /usr/bin/modem3g
$ sudo tar -zxvf sakis3g.tar.gz
$ sudo chmod +x sakis3g
$ sudo ./sakis3g connect
```

### Usage

Execute the below commands:

```sh
python3 servicecom.py start
python3 servicecom.py restart
python3 servicecom.py stop
```

For view the process use:
```sh
sudo ps -A | grep "python3"
```

and you will see python3 process running

For view the log on real time use:
```sh
tail -f servicecom.log
```