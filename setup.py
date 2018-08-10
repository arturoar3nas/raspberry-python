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
                print('[Setup.py][ERROR][prepare_dirs] Directory not created.')


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
        print("[Setup.py][INFO] Installing software...")
        os.system('apt-get install -y {0}'.format(' '.join(packages_to_install)))


def install_python_packages():
    # Now install packages
    for package in easy_install_list:
        print("[Setup.py][INFO] Installing %s" % package)
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
    if not os.path.exists('/usr/bin/modem3g'):
        os.chdir('/usr/bin/modem3g/')

    for files in untar_files:
        try:
            tar = tarfile.open(files)
            tar.extractall()
            tar.close()
        except:
            print("[Setup.py][ERROR][tar] There was an error opening tarfile. The file might be corrupt or missing.")


def install_daemon():
    try:
        with open('/etc/rc.local', 'rt') as file1:
            read_data = file1.read()
            lines = read_data.split('\n')
            for line in lines:
                if 'sudo python3 /home/pi/servicecom/servicecom.py start' in line:
                    print("[Setup.py][INFO][install_daemon] The daemon it's already installed")
                    return False
            file1.close()
        data = ""
        with open('/etc/rc.local', 'w') as file:
            for line in lines:
                if not 'exit 0' in line:
                    data += line + '\n'

            data += 'sudo python3 /home/pi/servicecom/servicecom.py start\n'
            data += 'exit 0\n'
            data += ''
            file.write(data)
            file.close()
            return True
    except IOError:
        raise Exception("[Setup.py][ERROR][install_daemon] Can't open or write file ")
        sys.exit(2)


def cptodir():
    i = 0
    while i < cp_files.__len__():
        try:
            if os.path.exists(cp_files[i]):
                copyfile(cp_files[i], cp_dest[i])
        except OSError:
            print('[Setup.py][ERROR][cptodir] Error copying file')
        i += 1

    for rmsrc in cp_files:
        try:
            if os.path.exists(rmsrc):
                os.remove(rmsrc)
        except OSError:
            print('[Setup.py][ERROR][cptodir] Error removing file')


def make_sure_sudo():
    ret = os.getuid()
    if ret != 0:
        print('[Setup.py][INFO][make_sure_sudo] You need root permissions to do this!')
        exit(1)


def deploy_software(update=True):
    prepare_dirs()
    download_things()
    install_packages(update)
    give_permission()
    tar()
    cptodir()
    os.chmod("/usr/bin/modem3g/sakis3g", 111)
    os.system("sudo chmod 777 /home/pi/servicecom")
    os.system("sudo chmod 777 /home/pi/servicecom/*")
    install_daemon()
    print('[Setup.py][INFO][deploy_software] Raspberry reboot now')
    os.system('sudo reboot now')


if __name__ == '__main__':
    make_sure_sudo()
    deploy_software()
