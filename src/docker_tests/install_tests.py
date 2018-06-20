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

    # install cower-git
    test_command(
        "aurman -S cower-git --noedit --pgp_fetch --keyserver keyserver.ubuntu.com --noconfirm")
    # check if cower-git installed
    test_command("pacman -Qi cower-git")

    # install repo package mu with double dashes
    test_command(
        "aurman -S --noedit --pgp_fetch --keyserver keyserver.ubuntu.com --noconfirm -- mu")
    # check if mu installed
    test_command("pacman -Qi mu")

    # search solutions to install mingw-w64-gcc
    test_command("aurmansolver -S mingw-w64-gcc")
    test_command("aurmansolver -S mingw-w64-gcc --deep_search")

    # search solutions to install ros-indigo-desktop-full
    test_command("aurmansolver -S ros-indigo-desktop-full")
    test_command("aurmansolver -S ros-indigo-desktop-full --deep_search")

    # install fprintd and libfprint-vfs0090-git
    test_command("aurman -S fprintd libfprint-vfs0090-git "
                 "--noedit --pgp_fetch --keyserver keyserver.ubuntu.com --noconfirm")

    # check if fprintd and libfprint-vfs0090-git are installed
    test_command("pacman -Qi fprintd")
    test_command("pacman -Qi libfprint-vfs0090-git")

    # install pacman-git
    test_command(
        "aurman -S pacman-git --noedit --pgp_fetch --keyserver keyserver.ubuntu.com --noconfirm")

    # check if pacman-git installed
    test_command("pacman -Qi pacman-git")

    exit(CurrentTest.to_return)
