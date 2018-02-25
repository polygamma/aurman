# aurman - AUR helper with almost pacman syntax

![](https://travis-ci.org/polygamma/aurman.svg?branch=master)

## aurman in the AUR

**aurman-git** *(https://aur.archlinux.org/packages/aurman-git)*

## Syntax
Pacman syntax with one exception: One has to put `--pk` in front of the packages,
so for example:

> aurman -Syu --pk package1 package2

> aurman -R --pk package1 package2 -sc

There are also aurman exclusive flags.

- `--noedit`: will not show changes of PKGBUILDs and .install files. just assumes you are okay with the changes.

- `--devel`: will fetch current development packages versions to decide whether a new version is available or not.

- `--deep_search`: dependency solving will ignore currently fulfilled dependencies of your system and try to solve the problem for a system with zero packages installed.
should almost never be needed, but if aurman is not able to find a solution to install packages, try rerunning aurman with this flag.
but be warned, it could take a few minutes to find solutions.

- `--pgp_fetch`: fetches needed pgp keys without asking the user

- `--keyserver name`: you may specify a keyserver to fetch the pgp keys from

- `--aur`: do things only for aur

- `--repo`: do things only for regular repo

- `--domain name`: change the base url for aur requests *(https://aur.archlinux.org is the default)*

## Features

  - threaded sudo loop in the background so you only have to enter your password once
  - reliable dependency resolving
  - conflict detection
  - split package support
  - development package support
  - distinction between explicitly and implicitly installed packages
  - let the user see and edit all needed PKGBUILDs before any of the building of AUR packages starts
  - fetching of needed pgp keys for package building
  - pacman --search for repo and aur packages (aur results sorted by user votes)

## Screenshots

#### dependency solving of complex packages:
![](https://user-images.githubusercontent.com/20651500/36606841-2c28de78-18c5-11e8-8df7-c123536121db.png)

#### showing errors of malformed aur packages:
![](https://user-images.githubusercontent.com/20651500/36606912-593c8c52-18c5-11e8-85f2-d38895c60e70.png)

#### deep_search flag yields new possibilities:
![](https://user-images.githubusercontent.com/20651500/36607016-aa9736e2-18c5-11e8-9684-59a4f3352746.png)

#### showing which changes will be made to the system:
![](https://user-images.githubusercontent.com/20651500/36607080-def95582-18c5-11e8-9030-df28efc2d180.png)

#### looking for needed pgp keys:
![](https://user-images.githubusercontent.com/20651500/36630164-32ba902c-1962-11e8-9cd5-044785660f21.png)

#### searching for packages:
![](https://user-images.githubusercontent.com/20651500/36643259-249bbccc-1a49-11e8-9fd6-aa752bc5b5ad.png)
