import os
from sys import exit

from docker_tests.test_utils import CurrentTest, test_command

if __name__ == '__main__':
    # change build dir
    test_command("mkdir -p /home/aurman/build_dir")
    test_command('sudo sh -c "{}"'
                 ''.format("echo 'BUILDDIR=/home/aurman/build_dir' >> /etc/makepkg.conf"))

    # install yay
    test_command("aurman -Syu yay --noedit --noconfirm")
    # check if yay installed
    test_command("pacman -Qi yay")

    if "yay" not in os.listdir("/home/aurman/build_dir"):
        print("Error: yay has not been built in build_dir")
        CurrentTest.to_return = 1
    else:
        print("Success: yay has been built in build_dir")

    # install pacman-git
    test_command("aurman -S pacman-git --noedit --noconfirm")

    # check if pacman-git installed
    test_command("pacman -Qi pacman-git")

    # change build dir again
    test_command('sudo sh -c "{}"'
                 ''.format("echo 'BUILDDIR=/home/aurman/build_dir' >> /etc/makepkg.conf"))

    # install yay-git
    test_command("aurman -S yay-git --noedit --noconfirm")
    # check if yay-git installed
    test_command("pacman -Qi yay-git")

    if "yay-git" not in os.listdir("/home/aurman/build_dir"):
        print("Error: yay-git has not been built in build_dir")
        CurrentTest.to_return = 1
    else:
        print("Success: yay-git has been built in build_dir")

    exit(CurrentTest.to_return)
