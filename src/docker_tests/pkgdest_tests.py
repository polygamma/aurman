from sys import exit

from docker_tests.test_utils import CurrentTest, test_command

if __name__ == '__main__':
    # change pkgdest dir
    test_command('sudo sh -c "{}"'
                 ''.format("echo 'PKGDEST=/tmp' >> /etc/makepkg.conf"))

    # install yay
    test_command(
        "aurman -Syu yay --noedit --noconfirm")
    # check if yay installed
    test_command("pacman -Qi yay")

    # change pkgdest dir in different makepkg.conf
    test_command("mkdir -p /home/aurman/build_dir")
    test_command('sudo sh -c "{}"'
                 ''.format("echo 'PKGDEST=/home/aurman/build_dir' > ~/.makepkg.conf"))

    # install pacman-git
    test_command(
        "aurman -S pacman-git --noedit --pgp_fetch --keyserver keyserver.ubuntu.com --noconfirm")

    # check if pacman-git installed
    test_command("pacman -Qi pacman-git")

    # install yay-git
    test_command(
        "aurman -S yay-git --noedit --noconfirm")
    # check if yay-git installed
    test_command("pacman -Qi yay-git")

    exit(CurrentTest.to_return)
