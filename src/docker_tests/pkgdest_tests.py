from sys import exit

from docker_tests.test_utils import CurrentTest, test_command

if __name__ == '__main__':

    # change pkgdest dir
    test_command('sudo sh -c "{}"'
                 ''.format("echo 'PKGDEST=/tmp' >> /etc/makepkg.conf"))

    # install cower
    test_command(
        "aurman -Syu cower --noedit --pgp_fetch --keyserver keyserver.ubuntu.com --noconfirm")
    # check if cower installed
    test_command("pacman -Qi cower")

    # change pkgdest dir in different makepkg.conf
    test_command("mkdir -p /home/aurman/build_dir")
    test_command('sudo sh -c "{}"'
                 ''.format("echo 'PKGDEST=/home/aurman/build_dir' > ~/.makepkg.conf"))

    # install pacman-git
    test_command(
        "aurman -S pacman-git --noedit --pgp_fetch --keyserver keyserver.ubuntu.com --noconfirm")

    # check if pacman-git installed
    test_command("pacman -Qi pacman-git")

    # install cower-git
    test_command(
        "aurman -S cower-git --noedit --pgp_fetch --keyserver keyserver.ubuntu.com --noconfirm")
    # check if cower-git installed
    test_command("pacman -Qi cower-git")

    exit(CurrentTest.to_return)
