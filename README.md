# aurman
AUR Helper

## now available in the AUR: https://aur.archlinux.org/packages/aurman-git

Syntax: This is a pacman wrapper, so it is basically pacman syntax. But one has to put *--pk* in front of the packages,
so for example:

**pacman -Syu package1 package2** -> **aurman -Syu --pk package1 package2**

**pacman -R package1 package2 -sc** -> **aurman -R --pk package1 package2 -sc**

There are also three aurman exclusive flags.

*--noedit* - will not show changes of PKGBUILDs and .install files. just assumes you are okay with the changes.

*--devel* - will fetch current development packages versions to decide whether a new version is available or not.

*--deep_search* - dependency solving will ignore currently fulfilled dependencies of your system and try to solve the problem for a system with zero packages installed. should almost never be needed, but if aurman is not able to find a solution to install packages, try rerunning aurman with this flag. but be warned, it could take a few minutes to find solutions.
