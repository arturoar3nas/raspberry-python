#!/usr/bin/python3

"""
# @file   servicecom.py
# @author Arturo Arenas (arturoar3nas@gmail.com)
# @date   12/06/18
# Brief:
    Script to install dependencies
  Usage:
    sudo python3 setup.py
"""


import os
import sys
import tarfile
from shutil import copyfile

simple_install = True

dirs_to_make = ['/home/pi/servicecom',
                '/usr/bin/modem3g'
                ]
things_to_download = ['http://raspberry-at-home.com/files/sakis3g.tar.gz']
dir_permission = ['/usr/bin/modem3g']
type_permission = [777]
untar_files = ['sakis3g.tar.gz']
apt_repos = []
packages_to_install = ['python3',
                       'python3-gpiozero',
                       'python-pip',
                       'python-dev',
                       'python3-psutil',
                       'ppp',
                       'python3-serial'
                       ]
# If is offline
cp_files = ['/home/pi/servicecom.py',
            '/home/pi/config.json',
            '/home/pi/Demo.py',
            '/home/pi/loadcellcmd.json',
            '/home/pi/loadcell.json',
            '/home/pi/networks.json',
            '/home/pi/scanwifi.py',
            '/home/pi/simstatus.json'
            ]
cp_dest = ['/home/pi/servicecom/servicecom.py',
           '/home/pi/servicecom/config.json',
           '/home/pi/servicecom/Demo.py',
           '/home/pi/servicecom/loadcellcmd.json',
           '/home/pi/servicecom/loadcell.json',
           '/home/pi/servicecom/networks.json',
           '/home/pi/servicecom/scanwifi.py',
           '/home/pi/servicecom/simstatus.json'
           ]

easy_install_list = []
git_repositories = []


def prepare_dirs():
    for dir in dirs_to_make:
        try:
            os.mkdir(dir)
        except OSError:
                print('Directory not created.')


def download_things():
    os.chdir('/usr/bin/modem3g/')
    for url in things_to_download:
        os.system('wget --no-check-certificate %s' % url)


def prepare_apt_repos():
    for repo in apt_repos:
        os.system('sudo add-apt-repository %s' % repo)


def install_packages(update=True):
    if update:
        os.system('apt-get update')
        print("Installing software...")
        os.system('apt-get install -y {0}'.format(' '.join(packages_to_install)))


def install_python_packages():
    # Now install packages
    for package in easy_install_list:
        print("Installing %s" % package)
        os.system('pip install {0}'.format(package))


def clone_git_repos():
    os.chdir('$HOME/src')
    for repo in git_repositories:
        name = os.path.splitext(os.path.split(repo)[1])[0]
        if os.system('test -d {0}'.format(name)).failed:
            os.system('git clone {0}'.format(repo))


def give_permission():
    for dirper in dir_permission:
        for mytype in type_permission:
            os.chmod(dirper, mytype)


def tar():
    os.chdir('/usr/bin/modem3g/')
    for files in untar_files:
        try:
            tar = tarfile.open(files)
            tar.extractall()
            tar.close()
        except:
            print("There was an error opening tarfile. The file might be corrupt or missing.")


def linecount_1(file):
    return len(open(file).readlines(  ))


def install_daemon():
    try:
        with open('/etc/rc.local', 'rt') as file1:
            read_data = file1.read()
            lines = read_data.split('\n')
            for line in lines:
                if 'sudo python3 /home/pi/servicecom/servicecom.py start' in line:
                    return False
            file1.close()

        with open('/etc/rc.local', 'a') as file:
            file.write('sudo python3 /home/pi/servicecom/servicecom.py start')
            file.write('')
            file.close()
            return True
    except IOError:
        raise Exception("Can't open or write file ")
        sys.exit(2);


def cptodir():
    i = 0
    while i < cp_files.__len__():
        try:
            copyfile(cp_files[i], cp_dest[i])
        except OSError:
            print('Error copying file')
        i += 1

    for rmsrc in cp_files:
        try:
            os.remove(rmsrc)
        except OSError:
            print('Error removing file')


def make_sure_sudo():
    ret = os.getuid()
    if ret != 0:
        print('You need root permissions to do this!')
        exit(1)


def deploy_software(update=True):
    prepare_dirs()
    download_things()
    install_packages(update)
    give_permission()
    tar()
    cptodir()
    os.chmod("/usr/bin/modem3g/sakis3g", 111)
    os.chmod('/home/pi/servicecom', 777)
    os.chmod('/home/pi/servicecom/*', 777)
    install_daemon()
    os.system('sudo reboot now')


if __name__ == '__main__':
    make_sure_sudo()
    deploy_software()
