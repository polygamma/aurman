#!/bin/bash

# source needed
for f in /etc/profile.d/*.sh; do source $f; done
source /etc/bash.bashrc
source /home/aurman/.bash_profile
source /home/aurman/.bashrc

# call test
python /home/aurman/aurman-git/$1
exit $?
