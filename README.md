# Servicecom.py

- [Features](#Usage)
- [Directories](#Usage)
- [Installation](#Usage)
- [Fast installer](#Usage)
- [Manual installer](#Usage)
- [Usage](#Usage)

## Service Communication Manager
  This Python Script Daemon do the below stuff:
  - Check the communication 3G
  - Check and Control the Status modem
  - Check the status application
  - Check the status info and create a json file
  - Managed Wi-Fi communication
  
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

## Directories

- in servicecom there:  servicecom.py and config.json
- in src there: all files needed

```sh
/home/pi $ 
├─── servicecom
│    └─── config.json  Demo.py  loadcellcmd.json  loadcell.json  networks.json  README.md  scanwifi.py  servicecom.py  setup.py                   simstatus.json  
```

### Installation

You will need the follows tools:

- [FileZilla](https://filezilla-project.org/)
- [Putty](https://putty.org/)

#### Fast installer
#### Online

```sh
sudo apt-get update
sudo apt-get install git
```
Then
```sh
sudo git clone https://github.com/arturoar3nas/raspberry-python && mv /home/pi/raspberry-python /home/pi/servicecom
```
Finally 
```sh
sudo python3 servicecom/setup.py 
```
If all it's fine, go to usage and enjoy!

#### Offline
Copy in the below directory: 

```sh
/home/pi/
```
The next Files:

- setup.py
- servicecom.py
- config.json
- Demo.py
- loadcellcmd.json
- loadcell.json
- networks.json
- scanwifi.py
- simstatus.json

Then you will need do:

```sh
sudo python3 setup.py 
```
Make sure to use the command with sudo. Wait to the installer
and later go to the [Usage](#Usage) step. 

#### Manual installer

#### Python

Servicecom requires [Python](https://www.python.org/) v3+ to run.
```sh
sudo apt-get install python3
sudo apt install python3-gpiozero
sudo apt install python3-psutil
```
#### Sakis3G

Servicecom requires [Sakis3G](http://raspberry-at-home.com/files/sakis3g.tar.gz).

Install the dependencies and Dependencies and start the modem.
```sh
sudo apt-get update
sudo apt-get install ppp
wget "http://raspberry-at-home.com/files/sakis3g.tar.gz"
sudo mkdir /usr/bin/modem3g
sudo chmod 777 /usr/bin/modem3g
sudo cp sakis3g.tar.gz /usr/bin/modem3g
cd /usr/bin/modem3g
sudo tar -zxvf sakis3g.tar.gz
sudo chmod +x sakis3g
sudo ./sakis3g connect
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
sudo ps -A | grep servicecom.py
```

and you will see python3 process running

For view the log on real time use:
```sh
tail -f /tmp/servicecom.log
```