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
    # install aurman
    test_command("sudo python setup.py install --optimize=1", "/home/aurman/aurman-git")

    # change pkgdest dir
    test_command('sudo sh -c "{}"'
                 ''.format("echo 'PKGDEST=/tmp' >> /etc/makepkg.conf"))

    # install cower
    test_command(
        "aurman -S cower --noedit --pgp_fetch --keyserver hkp://ipv4.pool.sks-keyservers.net:11371 --noconfirm")
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
