import os
from os import getcwd
from os.path import join
from sys import exit

from docker_tests.test_utils import CurrentTest, test_command

if __name__ == '__main__':
    # install expac-git
    test_command("git clone https://aur.archlinux.org/expac-git.git")
    test_command("makepkg -si --needed --noconfirm", dir_to_execute=join(getcwd(), "expac-git"))
    test_command("rm -rf expac-git/")

    # install aurman
    test_command("sudo python setup.py install --optimize=1", "/home/aurman/aurman-git")

    # install cower
    test_command(
        "aurman -Syu cower --noedit --pgp_fetch --keyserver keyserver.ubuntu.com --noconfirm")
    # check if cower installed
    test_command("pacman -Qi cower")
    # remove uninstalled packages
    test_command("aurman -Sc --aur --noconfirm")
    if os.path.isdir("/home/aurman/.cache/aurman/cower"):
        print("Success: cower cache dir has not been deleted")
    else:
        print("Error: cower cache dir has been deleted")
        CurrentTest.to_return = 1

    # install cower-git
    test_command(
        "aurman -S cower-git --noedit --pgp_fetch --keyserver keyserver.ubuntu.com --noconfirm")
    # check if cower-git installed
    test_command("pacman -Qi cower-git")

    # remove uninstalled packages
    test_command("aurman -Sc --aur --noconfirm")
    if os.path.isdir("/home/aurman/.cache/aurman/cower"):
        print("Error: cower cache dir has not been deleted")
        CurrentTest.to_return = 1
    else:
        print("Success: cower cache dir has been deleted")

    # remove all packages
    test_command("aurman -Scc --aur --noconfirm")
    if os.path.isdir("/home/aurman/.cache/aurman/cower-git"):
        print("Error: cower-git cache dir has not been deleted")
        CurrentTest.to_return = 1
    else:
        print("Success: cower-git cache dir has been deleted")

    exit(CurrentTest.to_return)
