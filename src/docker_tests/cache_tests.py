import os
from sys import exit

from docker_tests.test_utils import CurrentTest, test_command

if __name__ == '__main__':
    # install yay
    test_command("aurman -Syu yay --noedit --noconfirm")
    # check if yay installed
    test_command("pacman -Qi yay")
    # remove uninstalled packages
    test_command("aurman -Sc --aur --noconfirm")
    if os.path.isdir("/home/aurman/.cache/aurman/yay"):
        print("Success: yay cache dir has not been deleted")
    else:
        print("Error: yay cache dir has been deleted")
        CurrentTest.to_return = 1

    # install yay-git
    test_command("aurman -S yay-git --noedit --noconfirm")
    # check if yay-git installed
    test_command("pacman -Qi yay-git")

    # remove uninstalled packages
    test_command("aurman -Sc --aur --noconfirm")
    if os.path.isdir("/home/aurman/.cache/aurman/yay"):
        print("Error: yay cache dir has not been deleted")
        CurrentTest.to_return = 1
    else:
        print("Success: yay cache dir has been deleted")

    # remove all packages
    test_command("aurman -Scc --aur --noconfirm")
    if os.path.isdir("/home/aurman/.cache/aurman/yay-git"):
        print("Error: yay-git cache dir has not been deleted")
        CurrentTest.to_return = 1
    else:
        print("Success: yay-git cache dir has been deleted")

    exit(CurrentTest.to_return)
