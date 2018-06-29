#!/bin/bash

# source needed
for f in /etc/profile.d/*.sh; do source $f; done
source /etc/bash.bashrc
source /home/aurman/.bash_profile
source /home/aurman/.bashrc

# call test
if [[ -f $1 ]]; then
    python "$1"
else
    python -m docker_tests.$1
fi
exit $?
