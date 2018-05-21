from datetime import datetime, timedelta
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

    # set mirror to 30 days ago
    test_command("sudo mv /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.bak")
    d = (datetime.today() - timedelta(days=30)).date()
    test_command('sudo sh -c "{}"'
                 ''.format("echo '"
                           "Server = https://archive.archlinux.org/repos/"
                           "{}/{}/{}"
                           "/\$repo/os/\$arch"
                           "' > /etc/pacman.d/mirrorlist"
                           "".format(d.year, str(d.month).zfill(2), str(d.day).zfill(2))))

    # downgrade
    test_command("sudo pacman -Syyuu --noconfirm --force")

    # reset mirrors
    test_command("sudo mv /etc/pacman.d/mirrorlist.bak /etc/pacman.d/mirrorlist")
    test_command("sudo pacman -Syy")

    if run("pacman -Qqun", shell=True, stdout=DEVNULL, stderr=DEVNULL).returncode != 0:
        print("Error: there are no things to update")
        CurrentTest.to_return = 1
    else:
        print("Success: there are things to update")

    # update with aurman --do_everything
    test_command("aurman -Syu --do_everything --force --noconfirm"
                 " --noedit --pgp_fetch --keyserver hkp://ipv4.pool.sks-keyservers.net:11371")

    if run("pacman -Qqun", shell=True, stdout=DEVNULL, stderr=DEVNULL).returncode != 0:
        print("Success: everything known has been updated")
    else:
        print("Error: there are some things which are not updated")
        CurrentTest.to_return = 1

    exit(CurrentTest.to_return)
