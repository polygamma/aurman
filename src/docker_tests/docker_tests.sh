#!/bin/bash

function test_command
{

    RAW_COMMAND="$@"
    COMMAND="$RAW_COMMAND &> /dev/null"
    if eval $COMMAND; then
        echo "success with $RAW_COMMAND" >&2
    else
        echo "error with $RAW_COMMAND" >&2
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
test_command sudo python setup.py install --optimize=1

# install cower
test_command aurman -S cower --noconfirm --noedit --pgp_fetch --keyserver hkp://ipv4.pool.sks-keyservers.net:11371

# check if cower installed
test_command pacman -Qi cower

# search solution to install mingw-w64-gcc
test_command aurmansolver -S mingw-w64-gcc

if ${ANY_FAILED}; then exit 1; else exit 0; fi
