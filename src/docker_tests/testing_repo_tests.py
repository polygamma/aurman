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

    # activate testing
    test_command('sudo sh -c "{}"'
                 ''.format("sed -i '/\[testing\]/,/Include/s/^[ ]*#//' /etc/pacman.conf"))

    # update with aurman --do_everything
    test_command("aurman -Syu --do_everything"
                 " --noedit --pgp_fetch --keyserver hkp://ipv4.pool.sks-keyservers.net:11371 --noconfirm")

    if run("pacman -Qqun", shell=True, stdout=DEVNULL, stderr=DEVNULL).returncode != 0:
        print("Success: everything known has been updated")
    else:
        print("Error: there are some things which are not updated")
        CurrentTest.to_return = 1

    exit(CurrentTest.to_return)
