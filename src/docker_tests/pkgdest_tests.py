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

    # change pkgdest dir
    test_command('sudo sh -c "{}"'
                 ''.format("echo 'PKGDEST=/tmp' >> /etc/makepkg.conf"))

    # install cower
    test_command(
        "aurman -Syu cower --noedit --pgp_fetch --keyserver hkp://ipv4.pool.sks-keyservers.net:11371 --noconfirm")
    # check if cower installed
    test_command("pacman -Qi cower")

    # change pkgdest dir in different makepkg.conf
    test_command("mkdir -p /home/aurman/build_dir")
    test_command('sudo sh -c "{}"'
                 ''.format("echo 'PKGDEST=/home/aurman/build_dir' > ~/.makepkg.conf"))

    # install pacman-git
    test_command(
        "aurman -S pacman-git --noedit --pgp_fetch --keyserver hkp://ipv4.pool.sks-keyservers.net:11371 --noconfirm")

    # check if pacman-git installed
    test_command("pacman -Qi pacman-git")

    # install cower-git
    test_command(
        "aurman -S cower-git --noedit --pgp_fetch --keyserver hkp://ipv4.pool.sks-keyservers.net:11371 --noconfirm")
    # check if cower-git installed
    test_command("pacman -Qi cower-git")

    exit(CurrentTest.to_return)
