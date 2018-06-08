import os
from subprocess import run, DEVNULL
from sys import exit


class CurrentTest:
    to_return: int = 0


def test_command(command: str, dir_to_execute: str = None):
    if dir_to_execute is None:
        return_code = run(command, shell=True, stdout=DEVNULL, stderr=DEVNULL).returncode
    else:
        return_code = run(command, shell=True, stdout=DEVNULL, stderr=DEVNULL, cwd=dir_to_execute).returncode

    if return_code == 0:
        print("Success with: '{}'".format(command))
    else:
        print("Error with: '{}'".format(command))

    if CurrentTest.to_return == 0 and return_code != 0:
        CurrentTest.to_return = 1


if __name__ == '__main__':
    # install expac-git
    test_command("git clone https://aur.archlinux.org/expac-git.git")
    test_command("makepkg -si --needed --noconfirm", dir_to_execute="/home/aurman/expac-git")
    test_command("rm -rf expac-git/")

    # install aurman
    test_command("sudo python setup.py install --optimize=1", "/home/aurman/aurman-git")

    # install cower
    test_command(
        "aurman -Syu cower --noedit --pgp_fetch --keyserver hkp://ipv4.pool.sks-keyservers.net:11371 --noconfirm")
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
        "aurman -S cower-git --noedit --pgp_fetch --keyserver hkp://ipv4.pool.sks-keyservers.net:11371 --noconfirm")
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
