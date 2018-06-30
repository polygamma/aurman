import os
from sys import exit

from docker_tests.test_utils import CurrentTest, test_command

if __name__ == '__main__':

    # change build dir
    test_command("mkdir -p /home/aurman/build_dir")
    test_command('sudo sh -c "{}"'
                 ''.format("echo 'BUILDDIR=/home/aurman/build_dir' >> /etc/makepkg.conf"))

    # install cower
    test_command(
        "aurman -Syu cower --noedit --pgp_fetch --keyserver keyserver.ubuntu.com --noconfirm")
    # check if cower installed
    test_command("pacman -Qi cower")

    if "cower" not in os.listdir("/home/aurman/build_dir"):
        print("Error: cower has not been built in build_dir")
        CurrentTest.to_return = 1
    else:
        print("Success: cower has been built in build_dir")

    # install pacman-git
    test_command(
        "aurman -S pacman-git --noedit --pgp_fetch --keyserver keyserver.ubuntu.com --noconfirm")

    # check if pacman-git installed
    test_command("pacman -Qi pacman-git")

    # change build dir again
    test_command('sudo sh -c "{}"'
                 ''.format("echo 'BUILDDIR=/home/aurman/build_dir' >> /etc/makepkg.conf"))

    # install cower-git
    test_command(
        "aurman -S cower-git --noedit --pgp_fetch --keyserver keyserver.ubuntu.com --noconfirm")
    # check if cower-git installed
    test_command("pacman -Qi cower-git")

    if "cower-git" not in os.listdir("/home/aurman/build_dir"):
        print("Error: cower-git has not been built in build_dir")
        CurrentTest.to_return = 1
    else:
        print("Success: cower-git has been built in build_dir")

    exit(CurrentTest.to_return)
