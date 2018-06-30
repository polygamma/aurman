from subprocess import run, DEVNULL
from sys import exit

from docker_tests.test_utils import CurrentTest, test_command

if __name__ == '__main__':

    # activate testing
    test_command('sudo sh -c "{}"'
                 ''.format("sed -i '/\[testing\]/,/Include/s/^[ ]*#//' /etc/pacman.conf"))

    # update with aurman --do_everything
    test_command("aurman -Syu --do_everything"
                 " --noedit --pgp_fetch --keyserver keyserver.ubuntu.com --noconfirm")

    if run("pacman -Qqun", shell=True, stdout=DEVNULL, stderr=DEVNULL).returncode != 0:
        print("Success: everything known has been updated")
    else:
        print("Error: there are some things which are not updated")
        CurrentTest.to_return = 1

    exit(CurrentTest.to_return)
