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
import errno
from shutil import copyfile

# null = open(os.devnull,'wb')
# sys.stdout = null

simple_install = True

dirs_to_make = ['/home/pi/servicecom',
                '/home/pi/servicecom/src',
                '/usr/bin/modem3g'
                ]
things_to_download = ["http://raspberry-at-home.com/files/sakis3g.tar.gz"]
dir_permission = ["/usr/bin/modem3g"]
type_permission = [777]
untar_files = ["sakis3g.tar.gz"]
apt_repos = []
packages_to_install = ['python3',
                       'python3-gpiozero',
                       'python-pip',
                       'python-dev',
                       'python3-psutil',
                       'ppp'
                       ]
cp_files = ["/home/pi/servicecom.py",
            "/home/pi/config.json"
            ]
cp_dest = ["/home/pi/servicecom/servicecom.py",
           "/home/pi/servicecom/config.json"
           ]

easy_install_list = []
git_repositories = []


def prepare_dirs():
    try:
        for dir in dirs_to_make:
            os.mkdir(dir)
    except OSError as e:
        if e.errno == errno.EEXIST:
            print('Directory not created.')
        else:
            raise


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
        tar = tarfile.open(files)
        tar.extractall()
        tar.close()


def linecount_1(file):
    return len(open(file).readlines(  ))


def install_daemon():
    # sudo nano / etc / rc.local
    # sudo python / home / pi / sample.py &
    len = linecount_1("/etc/rc.local")
    f = open("/etc/rc.local", "r")
    contents = f.readlines()
    f.close()

    len -= 1
    contents.insert(len,"sudo python3 /home/pi/servicecom/servicecom.py start")

    f = open("path_to_file", "w")
    contents = "".join(contents)
    f.write(contents)
    f.close()
    return


def cptodir():
    try:
        for src in cp_files:
            for dst in cp_dest:
                copyfile(src, dst)
        for rmsrc in cp_files:
            os.remove(rmsrc)
    except OSError as e:
        if e.errno == errno.EEXIST:
            print('Error copying file')
        else:
            raise


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
    install_daemon()
    # reboot


if __name__ == '__main__':
    # make_sure_sudo()
    deploy_software()


