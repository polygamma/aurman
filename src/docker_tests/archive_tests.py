from datetime import datetime, timedelta
from os import getcwd
from os.path import join
from subprocess import run, DEVNULL
from sys import exit

from docker_tests.test_utils import CurrentTest, test_command

if __name__ == '__main__':
    # install expac-git
    test_command("git clone https://aur.archlinux.org/expac-git.git")
    test_command("makepkg -si --needed --noconfirm", dir_to_execute=join(getcwd(), "expac-git"))
    test_command("rm -rf expac-git/")

    # install aurman
    test_command("sudo python setup.py install --optimize=1", "/home/aurman/aurman-git")

    # set mirror to 7 days ago
    test_command("sudo mv /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.bak")
    d = (datetime.today() - timedelta(days=7)).date()
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
