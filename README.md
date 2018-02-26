# aurman - AUR helper with almost pacman syntax

![](https://travis-ci.org/polygamma/aurman.svg?branch=master)

## aurman in the AUR

**aurman-git** *(https://aur.archlinux.org/packages/aurman-git)*

## Syntax

##### Usage
aurman <operation> [ options ] [ target(s) ] - see also https://www.archlinux.org/pacman/pacman.8.html

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
- `-s`, `--search`
- `-u`, `--sysupgrade`
- `-y`, `--refresh`

##### the following native pacman options for `--sync` or `-S` will also be used by aurman for aur packages

- `--noconfirm`
- `--needed`
- `-s`, `--search`
- `-u`, `--sysupgrade`

##### aurman exclusive options for `--sync` or `-S`

- `--noedit`: will not show changes of PKGBUILDs and .install files. just assumes you are okay with the changes.

- `--devel`: will fetch current development packages versions to decide whether a new version is available or not.

- `--deep_search`: dependency solving will ignore currently fulfilled dependencies of your system and try to solve the problem for a system with zero packages installed.
should almost never be needed, but if aurman is not able to find a solution to install packages, try rerunning aurman with this flag.
but be warned, it could take a few minutes to find solutions.

- `--pgp_fetch`: fetches needed pgp keys without asking the user

- `--keyserver name`: you may specify a keyserver to fetch the pgp keys from

- `--aur`: do things only for aur

- `--repo`: do things only for regular repos

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
  - pacman --search for repo and aur packages (aur results sorted by popularity)

## Screenshots

#### dependency solving of complex packages:
![](https://user-images.githubusercontent.com/20651500/36660892-fbd4c0ea-1ad9-11e8-8496-16c9cb3000bb.png)

#### showing errors of malformed aur packages:
![](https://user-images.githubusercontent.com/20651500/36660903-0a36518a-1ada-11e8-93ef-3c40c6eccc9a.png)

#### deep_search flag yields new possibilities:
![](https://user-images.githubusercontent.com/20651500/36660920-139c17fa-1ada-11e8-9219-37c723915a88.png)

#### showing which changes will be made to the system:
![](https://user-images.githubusercontent.com/20651500/36660949-1f887d9c-1ada-11e8-9133-4bda3acb5e40.png)

#### looking for needed pgp keys:
![](https://user-images.githubusercontent.com/20651500/36660952-20816aba-1ada-11e8-9e7e-fb5f223460ae.png)

#### searching for packages:
![](https://user-images.githubusercontent.com/20651500/36660956-223b43c6-1ada-11e8-9178-eb106d73a81f.png)
