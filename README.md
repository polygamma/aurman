# aurman - AUR helper with almost pacman syntax

### **aurman** in the AUR: *aurman-git* (https://aur.archlinux.org/packages/aurman-git)

- **Syntax**:
Pacman syntax with one exception: One has to put *--pk* in front of the packages,
so for example:

*pacman -Syu package1 package2* to *aurman -Syu --pk package1 package2*

*pacman -R package1 package2 -sc* to *aurman -R --pk package1 package2 -sc*

There are three aurman exclusive flags.

- *--noedit* - will not show changes of PKGBUILDs and .install files. just assumes you are okay with the changes.

- *--devel* - will fetch current development packages versions to decide whether a new version is available or not.

- *--deep_search* - dependency solving will ignore currently fulfilled dependencies of your system and try to solve the problem for a system with zero packages installed.
should almost never be needed, but if aurman is not able to find a solution to install packages, try rerunning aurman with this flag.
but be warned, it could take a few minutes to find solutions.

- **Features**

  - threaded sudo loop in the background so you only have to enter your password once
  - reliable dependency resolving
  - conflict detection
  - split package support
  - development package support
  - distinction between explicitly and implicitly installed packages
  - let the user see and edit all needed PKGBUILDs before any of the building of AUR packages starts

- **Screenshots**
  - dependency solving of complex packages: ![screenshot from 2018-02-23 18-12-48](https://user-images.githubusercontent.com/20651500/36606841-2c28de78-18c5-11e8-8df7-c123536121db.png)
  - showing errors of malformed aur packages: ![screenshot from 2018-02-23 18-14-03](https://user-images.githubusercontent.com/20651500/36606912-593c8c52-18c5-11e8-85f2-d38895c60e70.png)
  - deep_search flag yields new possibilities: ![screenshot from 2018-02-23 18-16-18](https://user-images.githubusercontent.com/20651500/36607016-aa9736e2-18c5-11e8-9684-59a4f3352746.png)
  - showing which changes will be made to the system: ![screenshot from 2018-02-23 18-17-45](https://user-images.githubusercontent.com/20651500/36607080-def95582-18c5-11e8-9030-df28efc2d180.png)
