# aurman - AUR helper with syntax like pacman's

![](https://travis-ci.org/polygamma/aurman.svg?branch=master)

## aurman in the AUR

**aurman-git** *(https://aur.archlinux.org/packages/aurman-git)* - **development version**

**aurman** *(https://aur.archlinux.org/packages/aurman)* - **release version**

## Syntax

##### Usage
aurman < operation > [ options ] [ targets ] - see also https://www.archlinux.org/pacman/pacman.8.html

##### Description
aurman is a **pacman wrapper**.
All pacman operations are supported, and calling aurman with an operation besides `--sync` or `-S` will **pass the arguments to pacman**.

##### The following native pacman options for `--sync` or `-S` will be passed to pacman:

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

##### The following native pacman options for `--sync` or `-S` will also be used by aurman for aur packages:

- `--noconfirm`
- `--needed`
- `--ignore`
- `--ignoregroup`
- `-s`, `--search`
- `-u`, `--sysupgrade`
- `-c`, `--clean`

##### The following options are exclusive to aurman for `--sync` or `-S`:

- `--noedit`: Will not show changes of PKGBUILDs, .install, and other relevant files. It assumes users will be okay with the changes.

- `--always_edit`: Lets users edit the files of packages, even when there are no new changes.

- `--show_changes`: Will show changes of PKGBUILDs, .install, and other relevant files without asking.

- `--devel`: Will fetch current development versions of packages to check if a new version is available.

- `--deep_search`: Dependency solving will ignore currently fulfilled dependencies of users' systems and try to solve the problem for systems with zero packages installed.
If aurman is not able to find a solution to install packages, try re-running aurman with this flag.
It could take some time to find a solution.

- `--pgp_fetch`: Fetches needed PGP keys without asking the user.

- `--keyserver`: Lets users specify a keyserver to fetch the PGP keys from.

- `--aur`: Do things only for aur packages.

- `--repo`: Do things only for regular repos.

- `--domain`: Change the base url for aur requests *(https://aur.archlinux.org is the default)*

- `--solution_way`: Print what exactly will be done, order of installing/removing packages

- `--holdpkg`: Specify packages that are installed on users' systems that must not be removed.
Users may specify more than one package separated with spaces.

- `--holdpkg_conf`: Append packages from the pacman.conf to `--holdpkg`.

- `--do_everything`: `-u` for repo packages will be handled by `aurman`, not by `pacman`.
May be useful if (1) users use the `aurman` config to fetch repo packages from other repos than they would normally be installed from or
if (2) users want to confirm the installation of packages only once ("full batch interaction").
But this is **not** recommended since the pacman call `-Syu` will be split to `-Sy`, to do calculations, and to update the system.
With `aurman` handling `-u`, it still may result with a partial upgrade, not just because of splitting `-Syu`,
but because the dependency solver of `aurman` may yield wrong results.

- `--optimistic_versioning`: In case of an unknown version of a provider for a versioned dependency, assume that the dependency is fulfilled.

- `--rebuild`: Always rebuild packages before installing them.

## Config
Users may use the file `aurman_config` under `$XDG_CONFIG_HOME/aurman` (fallback to `~/.config/aurman` in case of no `$XDG_CONFIG_HOME`) as config for aurman.

### Config Options
#### Choose between multiple package sources
By default `aurman` assumes the following priorities in case of multiple available packages with the same names (high to low):
- Repository package as listed in the pacman.conf - see https://www.archlinux.org/pacman/pacman.conf.5.html#_repository_sections
> The order of repositories in the configuration files matters; repositories listed first will take precedence over those listed later in the file when packages in two repositories have identical names, regardless of version number.
- Aur packages

If one wants to override this priority, it has to be done via the aurman config.

For aur packages create a section  `[aur_packages]` and list the names of the aur packages.

For repo packages create a section `[repo_packages]` and list the names of the repo packages followed by `=` and the name of the repo.

> **Notice**: Those packages will be excluded from the `pacman --sysupgrade` by `--ignore`.
> Otherwise `pacman` would replace those packages.

Example:
```ini
[aur_packages]
aur_package_name
other_aur_package_name

[repo_packages]
repo_package_name=repo_one
other_repo_package_name=repo_two
```

#### PGP fetching keyserver
Users may specify the keyserver for PGP fetching in the config instead of yielding it via command line.

> **Notice**: Command line overrides config.

Create a key called `keyserver` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
keyserver=hkp://ipv4.pool.sks-keyservers.net:11371
```

#### Disable notifications about packages that are not in known repos or the aur
Create a key called `no_notification_unknown_packages` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
no_notification_unknown_packages
```

Users may also disable the notification for certain packages.

Create a section `[no_notification_unknown_packages]` and list the names of the packages.

Example:
```ini
[no_notification_unknown_packages]
package1_name
package2_name
```


#### Disable background sudo loop
Create a key called `no_sudo_loop` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
no_sudo_loop
```

#### Set the default for the question: `Do you want to see the changes of x?` to yes.
Create a key called `default_show_changes` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
default_show_changes
```

#### Ignore missing or incomplete arch fields in the build script, (passing `-A` to `makepkg` during package building)
Create a key called `ignore_arch` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
ignore_arch
```

#### Set names of packages to be treated as development packages
List the names of the packages in the section `[devel_packages]`.

Example:
```ini
[devel_packages]
package_name1
package_name2
```

#### Specify the folder to save `aurman` cache files
Create a key called `cache_dir` in the section `[miscellaneous]`.

default: `$XDG_CACHE_HOME/aurman` (fallback to `~/.cache/aurman` in case of no `$XDG_CACHE_HOME`).

Example:
```ini
[miscellaneous]
cache_dir=/tmp/aurman
```

#### Specify the timeout for AUR RPC requests in seconds
Create a key called `aur_timeout` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
aur_timeout=10
```

#### Use `--show_changes` persistently without specifying via commandline.
Create a key called `show_changes` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
show_changes
```

#### Use `--solution_way` persistently without specifying via commandline.
Create a key called `solution_way` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
solution_way
```

#### Use `--do_everything` persistently without specifying via commandline.
Create a key called `do_everything` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
do_everything
```

> **Notice**: This is **not** recommended since the usage of this flag is not recommended.

#### Use `--optimistic_versioning` persistently without specifying via commandline.
Create a key called `optimistic_versioning` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
optimistic_versioning
```

> **Notice**: This is **not** recommended since that flag should only be used when needed.

#### Set interval in which to call `sudo -v` (sudo loop) in seconds (default is 120)
Create a key called `sudo_timeout` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
sudo_timeout=120
```

#### Make use of the undocumented `--ask` flag of `pacman`
Create a key called `use_ask` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
use_ask
```

Explanation: see - https://git.archlinux.org/pacman.git/commit/?id=90e3e026d1236ad89c142b427d7eeb842bbb7ff4

`aurman` will use `--ask=4` if this config option is set.
This means the user will not have to confirm things like the installation of packages or the removal of conflicting packages again.
"Again" - meaning again for `pacman`.
User will still see the overview of `aurman`, predicting what will happen, which users will have to confirm unless using `--noconfirm`.
To make clear: `aurman` will predict what will happen in every case.
When using `--ask=4`, it may be possible that a conflict will not be detected by `aurman`. Hence, using `--ask=4` may lead
to unintended removal of package(s).
All in all it comes down to: "Redundant" confirmations of actions (less prone to errors but requires more user interactions)
or not confirming multiple times (but more prone to errors).


## Features

  - Threaded sudo loop in the background so users only have to enter their passwords once.
  - Reliable dependency resolving.
  - Conflict detection.
  - Split package support.
  - Development package support.
  - Distinction between explicitly and implicitly installed packages.
  - Lets users see and edit all needed PKGBUILDs before starting AUR package building.
  - Fetching of needed PGP keys for package building.
  - Pacman --search for repo and aur packages (aur results sorted by popularity).
  - Search function supports regex for searching the aur the first span of at least two consecutive non-regex
  characters being used. These results will be filtered by the regex expression afterwards.
  - Differentiate between the sources of packages in case of identical names in different known repos and/or the aur.

## Dependency solving description including benchmarks
https://github.com/polygamma/aurman/wiki/Description-of-the-aurman-dependency-solving

## Using aurman just as a dependency solver
https://github.com/polygamma/aurman/wiki/Using-aurman-as-dependency-solver

## FAQ
#### Question
`aurman` wants to remove packages that should not be removed - what's the matter?

#### Answer
Please check, if the problem arises, because `aurman` assumes `.so` dependencies to be unfulfilled.
*E.g.* `libavcodec.so=57-64` which requires a specific version of the mentioned `.so`.
This may be the case because the AUR package only lists `libavcodec.so` as being provided
without specifying the version. Hence `aurman` cannot be sure if the version will match,
since this can only be known after building the package, thus assuming that the dependency is not fulfilled.
Users may change this behavior by yielding `--optimistic_versioning` via the command line.
Now, `aurman` assumes the dependency will be fulfilled.
However, users should make sure that the version is going to be the needed one, otherwise
the behavior of installing the packages will be undefined.

This behavior may also occur when there are no `.so` dependencies involved.
Check if the dependencies are fulfilled.
If they are not fulfilled, because users forced installations of packages with `pacman -d`, this behavior is wanted.
It warns users about broken package dependencies in their systems.
To remove this output of `aurman` users have to fulfill the dependencies.


> **Notice**: `aurman` will **never** remove packages on its own. `aurman` just **predicts** what will happen.

#### Question
How do I change the editor used by `aurman` for editing PKGBUILDs etc.?

#### Answer
`aurman` uses the environment variables `VISUAL` and `EDITOR`. Users will have to change those variables.

If `VISUAL` is set, `aurman` uses this,

else if `EDITOR` is set, `aurman` uses this,

else `aurman` resorts to `/usr/bin/nano`.

#### Question
How to install packages whose names are saved in a file with `aurman`?

#### Answer
Users may use something like: `aurman -S $(cat ~/packages_names.txt | xargs)`.

#### Question
Does `aurman` support ignoring packages and groups via the `pacman.conf`?

#### Answer
Yes.

#### Question
I get a `UnicodeEncodeError` or a `UnicodeDecodeError` when executing `aurman` - how to fix it?

#### Answer
See: https://github.com/polygamma/aurman/issues/88.

#### Question
How to achieve `full batch interaction` with `aurman`?

#### Answer
Use `--do_everything` and `--ask` via the `aurman config`.

`--do_everything` for `2*` and `--ask` for `3*` as listed [here](https://wiki.archlinux.org/index.php/AUR_helpers#Active)

But there are downsides to this. See the description of `--do_everything` [here](https://github.com/polygamma/aurman#aurman-exclusive-options-for---sync-or--s)
and the description of `--ask` [here](https://github.com/polygamma/aurman#make-use-of-the-undocumented---ask-flag-of-pacman).

## Screenshots

![](https://i.imgur.com/VipYpfj.png)
![](https://i.imgur.com/uZYbNrS.gif)
