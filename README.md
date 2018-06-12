# aurman - AUR helper with almost pacman syntax

![](https://travis-ci.org/polygamma/aurman.svg?branch=master)

## aurman in the AUR

**aurman-git** *(https://aur.archlinux.org/packages/aurman-git)* - **development version**

**aurman** *(https://aur.archlinux.org/packages/aurman)* - **release version**

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

- `--noedit`: Will not show changes of PKGBUILDs, .install and other relevant files. just assumes you are okay with the changes.

- `--always_edit`: Lets the user edit the files of packages, even if there are no new changes.

- `--show_changes`: Will show changes of PKGBUILDs, .install and other relevant files without asking

- `--devel`: Will fetch current development packages versions to decide whether a new version is available or not.

- `--deep_search`: Dependency solving will ignore currently fulfilled dependencies of your system and try to solve the problem for a system with zero packages installed.
should almost never be needed, but if aurman is not able to find a solution to install packages, try rerunning aurman with this flag.
but be warned, it could take a few seconds to find solutions.

- `--pgp_fetch`: Fetches needed pgp keys without asking the user

- `--keyserver`: You may specify a keyserver to fetch the pgp keys from

- `--aur`: Do things only for aur

- `--repo`: Do things only for regular repos

- `--domain`: Change the base url for aur requests *(https://aur.archlinux.org is the default)*

- `--solution_way`: Print what exactly will be done, order of installing/removing packages

- `--holdpkg`: Specify packages which are installed on your system but must not be removed.
you may specify more than one package, space separated

- `--holdpkg_conf`: Append packages from the pacman.conf to `--holdpkg`

- `--do_everything`: `-u` for repo packages will also be handled by `aurman`, not by `pacman`.
may be useful if you are using the `aurman` config to fetch repo packages from other repos than they would normally be installed from.
may also be useful, if one wants to confirm the installation of packages only once, also known as "full batch interaction".
but this is in general **not** recommended, since the pacman call `-Syu` is being split to `-Sy`, do calculations, update the system.
since `aurman` is handling `-u` in that case, it is also possible to have a partial upgrade, not only because of splitting `-Syu`,
but also because of the possibility that the dependency solver of `aurman` yields a wrong result and thus leads to a partial upgrade.

- `--optimistic_versioning`: In case of an unknown version of a provider for a versioned dependency, assume that the dependency is fulfilled

- `--rebuild`: Always rebuild packages before installing them

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

> **Notice**: Those packages will be excluded from the `pacman --sysupgrade` by `--ignore`.
> Otherwise `pacman` would replace those packages

Example:
```ini
[aur_packages]
aur_package_name
other_aur_package_name

[repo_packages]
repo_package_name=repo_one
other_repo_package_name=repo_two
```

#### pgp fetching keyserver
you may specify the keyserver for pgp fetching in the config instead of yielding it via command line.

> **Notice**: command line overrides config

create a key called `keyserver` in the section `[miscellaneous]` to do that.

Example:
```ini
[miscellaneous]
keyserver=hkp://ipv4.pool.sks-keyservers.net:11371
```

#### disable notification about packages neither in known repos nor in the aur
create a key called `no_notification_unknown_packages` in the section `[miscellaneous]` to do that.

Example:
```ini
[miscellaneous]
no_notification_unknown_packages
```

you may also disable the notification for single packages only.

create a section `[no_notification_unknown_packages]` and list the names of the packages as values

Example:
```ini
[no_notification_unknown_packages]
package1_name
package2_name
```


#### disable background sudo loop
create a key called `no_sudo_loop` in the section `[miscellaneous]` to do that.

Example:
```ini
[miscellaneous]
no_sudo_loop
```

#### Set the default for the question: `Do you want to see the changes of x?` to yes
create a key called `default_show_changes` in the section `[miscellaneous]` to do that.

Example:
```ini
[miscellaneous]
default_show_changes
```

#### Ignore a missing or incomplete arch field in the build script, which means: pass `-A` to `makepkg` during building of packages
create a key called `ignore_arch` in the section `[miscellaneous]` to do that.

Example:
```ini
[miscellaneous]
ignore_arch
```

#### Set names of packages to be treated as development packages
list the names of the packages in the section `[devel_packages]` to do that

Example:
```ini
[devel_packages]
package_name1
package_name2
```

#### Specify the folder to save `aurman` cache files
create a key called `cache_dir` in the section `[miscellaneous]` to do that.

default: `$XDG_CACHE_HOME/aurman` (fallback to `~/.cache/aurman` in case of no `$XDG_CACHE_HOME`).

Example:
```ini
[miscellaneous]
cache_dir=/tmp/aurman
```

#### Specify the timeout for AUR RPC requests in seconds
create a key called `aur_timeout` in the section `[miscellaneous]` to do that.

Example:
```ini
[miscellaneous]
aur_timeout=10
```

#### Use `--show_changes` persistently without the need to specify it via the commandline
create a key called `show_changes` in the section `[miscellaneous]` to do that.

Example:
```ini
[miscellaneous]
show_changes
```

#### Use `--solution_way` persistently without the need to specify it via the commandline
create a key called `solution_way` in the section `[miscellaneous]` to do that.

Example:
```ini
[miscellaneous]
solution_way
```

#### Use `--do_everything` persistently without the need to specify it via the commandline
create a key called `do_everything` in the section `[miscellaneous]` to do that.

Example:
```ini
[miscellaneous]
do_everything
```

> **Notice**: This is **not** recommended, since the usage of that flag is in general not recommended.

#### Use `--optimistic_versioning` persistently without the need to specify it via the commandline
create a key called `optimistic_versioning` in the section `[miscellaneous]` to do that.

Example:
```ini
[miscellaneous]
optimistic_versioning
```

> **Notice**: This is **not** recommended, since that flag should only be used if needed

#### Set interval in which to call `sudo -v` (sudo loop) in seconds, default is 120
create a key called `sudo_timeout` in the section `[miscellaneous]` to do that.

Example:
```ini
[miscellaneous]
sudo_timeout=120
```

#### Make use of the undocumented `--ask` flag of `pacman`
create a key called `use_ask` in the section `[miscellaneous]` to do that.

Example:
```ini
[miscellaneous]
use_ask
```

Explanation: see - https://git.archlinux.org/pacman.git/commit/?id=90e3e026d1236ad89c142b427d7eeb842bbb7ff4

`aurman` is going to use `--ask=4`, if this config option is set.
That means, that the user does not have to confirm e.g. the installation of packages, or the removal of conflicting packages, again.
"Again" - meaning again for `pacman`.
The user still sees the overview of `aurman`, predicting what is going to happen, which the user has to confirm,
unless using `--noconfirm`.
To make it very clear: `aurman` is only predicting what is going to happen, in every case.
When using `--ask=4`, it is possible, that an upcoming conflict is not detected by `aurman`, hence using `--ask=4` leading
to the removal of a package, the user did not want to get removed.
All in all it comes down to: "Redundant" confirmations of actions, which is less sensitive to errors, but requires more user interactions,
or not confirming multiple times, which is more sensitive to errors.


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

## FAQ
#### Question
`aurman` wants to remove packages, which should not be removed, what's the matter?

#### Answer
Please check, if the problem arises, because `aurman` assumes `.so` dependencies to be unfulfilled.
E. g. `libavcodec.so=57-64` which requires a specific version of the mentioned `.so`.
This may be the case, because a providing AUR package only lists `libavcodec.so` as being provided,
without specifying the version. Hence `aurman` cannot be sure, if the version will match,
since this can only be known after building the package, thus assumes that the dependency is not fulfilled.
You may change this behavior by yielding `--optimistic_versioning` via the command line,
in that case `aurman` assumes the dependency to be fulfilled.
You should make sure, that the version is going to be the needed one, otherwise
the behavior of installing the packages is undefined.

This behavior of `aurman` may even occur, if there are no `.so` dependencies involved.
In that case check, if the dependencies are *really* fulfilled on your system.
If they are not, because you forced installations of packages with `pacman -d`, that behavior of `aurman` is explicitly wanted.
It warns you about broken package dependencies of your system.
To remove that output of `aurman` you have to fulfill the dependencies.


> **Notice**: `aurman` will **never** remove packages on its own, `aurman` just **predicts** what is going to happen

#### Question
How do I change the editor used by `aurman` for editing PKGBUILDs etc.?

#### Answer
`aurman` uses the environment variables `VISUAL` and `EDITOR`, hence you have to change those variables.

If `VISUAL` is set, `aurman` uses that,

else if `EDITOR` is set, `aurman` uses that,

else `aurman` uses `/usr/bin/nano`

#### Question
How to install packages whose names are saved in a file with `aurman`?

#### Answer
You may simply use something like: `aurman -S $(cat ~/packages_names.txt | xargs)`

#### Question
Does `aurman` support ignoring packages and groups via the `pacman.conf`?

#### Answer
Yes

#### Question
I get a `UnicodeEncodeError` or a `UnicodeDecodeError` when executing `aurman` - how to fix it?

#### Answer
see: https://github.com/polygamma/aurman/issues/88

## Screenshots

![](https://i.imgur.com/VipYpfj.png)
![](https://i.imgur.com/uZYbNrS.gif)
