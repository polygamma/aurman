#!/bin/bash

function test_command
{

    COMMAND="python /home/aurman/aurman-git/src/docker_tests/execute_command.py '$1'"
    if eval $COMMAND; then
        echo "success with: '$1'" >&2
    else
        echo "error with: '$1'" >&2
        ANY_FAILED=true
    fi
}

ANY_FAILED=false

# source needed
for f in /etc/profile.d/*.sh; do source $f; done
source /etc/bash.bashrc
source /home/aurman/.bash_profile
source /home/aurman/.bashrc

# install aurman
cd /home/aurman/aurman-git
test_command "sudo python setup.py install --optimize=1"

# install cower
test_command "aurman -S cower --noconfirm --noedit --pgp_fetch --keyserver hkp://ipv4.pool.sks-keyservers.net:11371"

# check if cower installed
test_command "pacman -Qi cower"

# install cower-git
test_command "yes | aurman -S cower-git --noedit --pgp_fetch --keyserver hkp://ipv4.pool.sks-keyservers.net:11371"

# check if cower-git installed
test_command "pacman -Qi cower-git"

# search solutions to install mingw-w64-gcc
test_command "aurmansolver -S mingw-w64-gcc"
test_command "aurmansolver -S mingw-w64-gcc --deep_search"

# search solutions to install ros-indigo-desktop-full
test_command "aurmansolver -S ros-indigo-desktop-full"
test_command "aurmansolver -S ros-indigo-desktop-full --deep_search"

# install fprintd and libfprint-vfs0090-git
test_command "yes | aurman -S fprintd libfprint-vfs0090-git --noedit --pgp_fetch --keyserver hkp://ipv4.pool.sks-keyservers.net:11371"

# check if fprintd and libfprint-vfs0090-git are installed
test_command "pacman -Qi fprintd"
test_command "pacman -Qi libfprint-vfs0090-git"

# install pacman-git
test_command "yes | aurman -S pacman-git --noedit --pgp_fetch --keyserver hkp://ipv4.pool.sks-keyservers.net:11371"

# check if pacman-git installed
test_command "pacman -Qi pacman-git"

if ${ANY_FAILED}; then exit 1; else exit 0; fi
