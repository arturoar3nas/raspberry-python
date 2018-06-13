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

# null = open(os.devnull,'wb')
# sys.stdout = null

simple_install = True

dirs_to_make        = ['/home/pi/servicecom','/home/pi/servicecom/src','/usr/bin/modem3g']
things_to_download  = ["http://raspberry-at-home.com/files/sakis3g.tar.gz"]
apt_repos           = []
packages_to_install = ['python3',
                       'python3-gpiozero',
                       'python-pip',
                       'python-dev',
                       'python3-psutil',
                       'ppp']

easy_install_list   = []
git_repositories    = []


def prepare_dirs():
    for dir in dirs_to_make:
        os.mkdir(dir)


def download_things():
    for url in things_to_download:
        with os.chdir('/home/pi/servicecom/src'):
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


def deploy_software(update=True):
    prepare_dirs()
    download_things()
    prepare_apt_repos()
    install_packages(update)
    install_python_packages()
    clone_git_repos()


if __name__ == '__main__':
    deploy_software()
