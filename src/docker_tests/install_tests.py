from sys import exit

from docker_tests.test_utils import CurrentTest, test_command

if __name__ == '__main__':
    # install yay
    test_command("aurman -Syu yay --noedit --noconfirm")
    # check if yay installed
    test_command("pacman -Qi yay")

    # install yay-git
    test_command("aurman -S yay-git --noedit --noconfirm")
    # check if yay-git installed
    test_command("pacman -Qi yay-git")

    # install repo package mu with double dashes
    test_command("aurman -S --noedit --noconfirm -- mu")
    # check if mu installed
    test_command("pacman -Qi mu")

    # search solutions to install mingw-w64-gcc
    test_command("aurmansolver -S mingw-w64-gcc")
    test_command("aurmansolver -S mingw-w64-gcc --deep_search")

    # search solutions to install ros-lunar-desktop-full
    test_command("aurmansolver -S ros-lunar-desktop-full")
    test_command("aurmansolver -S ros-lunar-desktop-full --deep_search")

    # install fprintd and libfprint-vfs0090-git
    test_command("aurman -S fprintd libfprint-vfs0090-git --noedit --noconfirm")

    # check if fprintd and libfprint-vfs0090-git are installed
    test_command("pacman -Qi fprintd")
    test_command("pacman -Qi libfprint-vfs0090-git")

    # install pacman-git
    test_command("aurman -S pacman-git --noedit --noconfirm")

    # check if pacman-git installed
    test_command("pacman -Qi pacman-git")

    exit(CurrentTest.to_return)
