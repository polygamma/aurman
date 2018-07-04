from datetime import datetime, timedelta
from subprocess import run, DEVNULL
from sys import exit

from docker_tests.test_utils import CurrentTest, test_command

if __name__ == '__main__':
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
    test_command("sudo pacman -Syyuu --noconfirm --overwrite '*'")

    # reset mirrors
    test_command("sudo mv /etc/pacman.d/mirrorlist.bak /etc/pacman.d/mirrorlist")
    test_command("sudo pacman -Syy")

    if run("pacman -Qqun", shell=True, stdout=DEVNULL, stderr=DEVNULL).returncode != 0:
        print("Error: there are no things to update")
        CurrentTest.to_return = 1
    else:
        print("Success: there are things to update")

    # update with aurman --do_everything
    test_command("aurman -Syu --do_everything --overwrite '*' --noconfirm --noedit")

    if run("pacman -Qqun", shell=True, stdout=DEVNULL, stderr=DEVNULL).returncode != 0:
        print("Success: everything known has been updated")
    else:
        print("Error: there are some things which are not updated")
        CurrentTest.to_return = 1

    exit(CurrentTest.to_return)
