#!/bin/bash

cd /home/aurman/aurman-git
sudo python setup.py install --optimize=1
cd /home/aurman
sudo rm -rf aurman-git/

# fails because of subprocess.run?
aurman -S cower --noconfirm --noedit --pgp_fetch --keyserver hkp://ipv4.pool.sks-keyservers.net:11371
