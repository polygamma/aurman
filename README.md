# aurman - AUR helper with almost pacman syntax

![](https://travis-ci.org/polygamma/aurman.svg?branch=master)

## aurman in the AUR

**aurman-git** *(https://aur.archlinux.org/packages/aurman-git)*

## Syntax

##### Usage
aurman < operation > [ options ] [ targets ] - see also https://www.archlinux.org/pacman/pacman.8.html

##### Description
aurman is meant as a **pacman wrapper**.
All pacman operations are supported, but calling aurman with an operation besides `--sync` or `-S` will **just pass the arguments to pacman**.

##### the following native pacman options for `--sync` or `-S` will be forwarded to pacman

- `-r`, `--root`
- `-v`, `--verbose`
- `--cachedir`
- `--color`
- `--debug`
- `--gpgdir`
- `--hookdir`
- `--logfile`
- `--noconfirm`
- `--confirm`
- `--force`
- `--asdeps`
- `--asexplicit`
- `--needed`
- `--ignore`
- `--ignoregroup`
- `-s`, `--search`
- `-u`, `--sysupgrade`
- `-y`, `--refresh`

##### the following native pacman options for `--sync` or `-S` will also be used by aurman for aur packages

- `--noconfirm`
- `--needed`
- `--ignore`
- `--ignoregroup`
- `-s`, `--search`
- `-u`, `--sysupgrade`

##### aurman exclusive options for `--sync` or `-S`

- `--noedit`: will not show changes of PKGBUILDs and .install files. just assumes you are okay with the changes.

- `--devel`: will fetch current development packages versions to decide whether a new version is available or not.

- `--deep_search`: dependency solving will ignore currently fulfilled dependencies of your system and try to solve the problem for a system with zero packages installed.
should almost never be needed, but if aurman is not able to find a solution to install packages, try rerunning aurman with this flag.
but be warned, it could take a few seconds to find solutions.

- `--pgp_fetch`: fetches needed pgp keys without asking the user

- `--keyserver name`: you may specify a keyserver to fetch the pgp keys from

- `--aur`: do things only for aur

- `--repo`: do things only for regular repos

- `--domain name`: change the base url for aur requests *(https://aur.archlinux.org is the default)*

- `--solution_way`: print what exactly will be done, order of installing/removing packages

- `--holdpkg name`: specify packages which are installed on your system but must not be removed.
you may specify more than one package, space separated

- `--holdpkg_conf`: append packages from the pacman.conf to `--holdpkg`

## Features

  - threaded sudo loop in the background so you only have to enter your password once
  - reliable dependency resolving
  - conflict detection
  - split package support
  - development package support
  - distinction between explicitly and implicitly installed packages
  - let the user see and edit all needed PKGBUILDs before any of the building of AUR packages starts
  - fetching of needed pgp keys for package building
  - pacman --search for repo and aur packages (aur results sorted by popularity)

## Dependency solving description including benchmarks
https://github.com/polygamma/aurman/wiki/Description-of-the-aurman-dependency-solving

## Using aurman just as dependency solver
https://github.com/polygamma/aurman/wiki/Using-aurman-as-dependency-solver

## Screenshots

![](https://i.imgur.com/VipYpfj.png)
![](https://i.imgur.com/uZYbNrS.gif)
