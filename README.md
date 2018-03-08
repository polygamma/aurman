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
- `-c`, `--clean`

##### the following native pacman options for `--sync` or `-S` will also be used by aurman for aur packages

- `--noconfirm`
- `--needed`
- `--ignore`
- `--ignoregroup`
- `-s`, `--search`
- `-u`, `--sysupgrade`
- `-c`, `--clean`

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

- `--do_everything`: `-u` for repo packages will also be handled by `aurman`, not by `pacman`.
may be useful if you are using the `aurman` config to fetch repo packages from other repos than they would normally be installed from.
this is in general **not** recommended!

## Config
You may use the file `aurman_config` under `$XDG_CONFIG_HOME/aurman` (fallback to `~/.config/aurman` in case of no `$XDG_CONFIG_HOME`) as config for aurman.

### config options
#### choose between multiple package sources
By default `aurman` assumes the following priorities in case of multiple available packages with the same names (high to low):
- repository package as listed in the pacman.conf - see https://www.archlinux.org/pacman/pacman.conf.5.html#_repository_sections
> The order of repositories in the configuration files matters; repositories listed first will take precedence over those listed later in the file when packages in two repositories have identical names, regardless of version number.
- aur packages

If one wants to override this priority, it has to be done via the aurman config.

For aur packages create a section  `[aur_packages]` and list the names of the aur packages.

For repo packages create a section `[repo_packages]` and list the names of the repo packages followed by `=` and the name of the repo.

Example:
```ini
[aur_packages]
aur_package_name
other_aur_package_name

[repo_packages]
repo_package_name=repo_one
other_repo_package_name=repo_two
```


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
  - search function supports regex. for searching the aur the first span of at least two consecutive non-regex
  characters is being used. these results are being filtered by the regex expression afterwards.
  - differentiate between the possible sources to install packages from in case of same names in different known repos and/or the aur

## Dependency solving description including benchmarks
https://github.com/polygamma/aurman/wiki/Description-of-the-aurman-dependency-solving

## Using aurman just as dependency solver
https://github.com/polygamma/aurman/wiki/Using-aurman-as-dependency-solver

## Screenshots

![](https://i.imgur.com/VipYpfj.png)
![](https://i.imgur.com/uZYbNrS.gif)
