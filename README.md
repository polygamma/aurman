# aurman - AUR helper with almost pacman syntax

[![Build Status](https://travis-ci.org/polygamma/aurman.svg?branch=master)](https://travis-ci.org/polygamma/aurman)
[![aurman](https://img.shields.io/aur/version/aurman.svg?label=aurman)](https://aur.archlinux.org/packages/aurman/)
[![aurman-git](https://img.shields.io/aur/version/aurman-git.svg?label=aurman-git)](https://aur.archlinux.org/packages/aurman-git/)
[![GitHub license](https://img.shields.io/github/license/polygamma/aurman.svg)](https://github.com/polygamma/aurman/blob/master/LICENSE)


## aurman in the AUR

**aurman-git** *(https://aur.archlinux.org/packages/aurman-git)* - **development version**

**aurman** *(https://aur.archlinux.org/packages/aurman)* - **release version**

> **Notice**: Even though it may seem like an AUR helper is targeted at inexperienced users, the opposite is the case.
> `aurman` is targeted at **advanced** users, who are familiar with `pacman`, `makepkg` and most of all with the `AUR`.
> `aurman` is an AUR **helper**, it can't and will never be a replacement for the sometimes needed concept of "human interaction".
> If you **ever** encounter an issue whereby `aurman` e.g. is not able to find a dependency solution, and you do not know
> how to solve the problem  **either**, you should **not** use an AUR helper. Even though the specific problem may be a bug in the `aurman`
> implementation, it is **always** expected that you as a [Turing-complete user](http://contemporary-home-computing.org/turing-complete-user/) know what to do. If you do not, do not use `aurman`.
> Also: If you are already failing to install `aurman`, because you do not know e. g. how to import PGP keys or how to fulfill `aurman`
> dependencies manually, you should **not** use `aurman`.
> Last but not least: The GitHub issues are **not** for support, they are **only** for feature requests, bug reports or general discussions.
> To reduce the noise by users who should not use `aurman`, but still do, users who fill out issues in a non-sensible way
> may be banned from this repository without further warning

## Syntax

##### Usage
aurman < operation > [ options ] [ targets ] - see also https://www.archlinux.org/pacman/pacman.8.html

##### Description
aurman is a **pacman wrapper**.
All pacman operations are supported, and calling aurman with an operation besides `--sync` or `-S` **passes the arguments to pacman**.

##### Native pacman options for `--sync` or `-S` that are passed to pacman:

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
- `--overwrite`
- `--asdeps`
- `--asexplicit`
- `--needed`
- `--ignore`
- `--ignoregroup`
- `-s`, `--search`
- `-i`, `--info`
- `-u`, `--sysupgrade`
- `-y`, `--refresh`
- `-c`, `--clean`

##### Native pacman options for `--sync` or `-S` that are also used by aurman:

- `--color` - Note: By default, `aurman` respects the presence of the `Color` option in `pacman.conf`.
- `--noconfirm`
- `--needed`
- `--ignore`
- `--ignoregroup`
- `-s`, `--search`
- `-i`, `--info`
- `-u`, `--sysupgrade`
- `-c`, `--clean`

##### Options for `--sync` or `-S` exclusive to aurman:

- `--noedit`: Do not show changes of PKGBUILDs, .install, and other relevant files. It assumes you will be okay with the changes.

- `--always_edit`: Edit the files of packages even when there are no new changes.

- `--show_changes`: Show changes of PKGBUILDs, .install, and other relevant files without asking.

- `--devel`: Fetch current development versions of packages to check if a new version is available.

- `--deep_search`: Dependency solving will ignore currently fulfilled dependencies and try to solve the problem for systems with zero packages installed.
If aurman is not able to find a solution, try re-running with this flag.
It could take some time to find a solution.

- `--pgp_fetch`: Fetch needed PGP keys without asking.

- `--keyserver`: Specify a keyserver to fetch the PGP keys from.

- `--aur`: `-Ss` just searches for AUR packages and `-Sc` cleans only the `aurman` cache.

- `--repo`: `-Ss` just searches for repo packages and `-Sc` cleans only the `pacman` cache.

- `--domain`: Change the base URL for AUR requests *(https://aur.archlinux.org is the default)*.

- `--solution_way`: Print what exactly will be done (order of installing/removing packages).

- `--holdpkg`: Specify installed packages that must not be removed.
Separate package names with space to specify more than one package.

- `--holdpkg_conf`: Append packages from the pacman.conf to `--holdpkg`.

- `--do_everything`: `-u` for repo packages will be handled by `aurman` and not `pacman`.
May be useful if (1) the `aurman` config is used to fetch repo packages from other repos than they would normally be installed from or
if (2) you want to confirm the installation of packages only once ("full batch interaction").
This is **not** recommended since the pacman call `-Syu` is executed in this
order: split to `-Sy`, do calculations, and upgrade the system.
With `aurman` handling `-u`, it still may result in a partial upgrade, not just because of splitting `-Syu`,
but because the dependency solver of `aurman` may yield wrong results.

- `--optimistic_versioning`: In case of an unknown version of a provider for a versioned dependency, assume that the dependency is fulfilled.

- `--rebuild`: Always rebuild packages before installing them.

- `--sort_by_name`: Sort `-Ss` AUR results by name.

- `--sort_by_votes`: Sort `-Ss` AUR results by votes.

- `--sort_by_popularity`: Sort `-Ss` AUR results by popularity.

- `--skip_news`: Skips being shown unseen `archlinux.org` news.

- `--skip_new_locations`: Skips being shown new locations of packages.

- `--devel_skip_deps`: Skips dependency checks when determining development packages versions (`makepkg -odc` instead of `makepkg -oc`)

## Config and cache directory
`aurman` conforms to the [XDG Base Directory Specification](https://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html):
- The configuration file is `$XDG_CONFIG_HOME/aurman/aurman_config`
- The cache directory used to remember internal state and to store downloaded AUR package sources is `$XDG_CACHE_HOME/aurman/`

### Config Options
#### Command-line defaults
A number of `aurman`'s command-line flags can be enabled by default, by listing them with the leading `--` removed in the `[miscellaneous]` section. In a case of conflict between a command-line flag and a config option, the command-line flag always wins.

Available (example) defaults:
```ini
[miscellaneous]
keyserver=hkp://ipv4.pool.sks-keyservers.net:11371
show_changes
solution_way
do_everything
optimistic_versioning
skip_news
skip_new_locations
```

> **Notice**: Use of `do_everything` is **not** recommended since the usage of this flag is in general not recommended.

> **Notice**: Use of `optimistic_versioning` is **not** recommended since this flag should only be used when needed.

#### Choose between multiple package sources
By default `aurman` assumes the following priorities in a case where multiple packages with the same names are available (high to low):
- Repository package as listed in the pacman.conf - see https://www.archlinux.org/pacman/pacman.conf.5.html#_repository_sections
> The order of repositories in the configuration file matters; repositories listed first will take precedence over those listed later in the file when packages in two repositories have identical names, regardless of version number.
- AUR packages

Overriding this priority has to be done via the aurman config.

For AUR packages create a section  `[aur_packages]` and list the names of the AUR packages.

For repo packages create a section `[repo_packages]` and list the names of the repo packages followed by `=` and the name of the repo.

> **Notice**: These packages will be excluded from the `pacman --sysupgrade` by `--ignore`.
> Otherwise `pacman` would replace these packages.

Example:
```ini
[aur_packages]
aur_package_name
other_aur_package_name

[repo_packages]
repo_package_name=repo_one
other_repo_package_name=repo_two
```

#### Disable notifications about packages that are not in known repos or the AUR
Create a key called `no_notification_unknown_packages` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
no_notification_unknown_packages
```

You may also disable the notification for certain packages.

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

#### Set the preselected answer for the question: `Do you want to see the changes of x?` to `yes`.
Create a key called `default_show_changes` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
default_show_changes
```

> **Notice**: Not setting this option retains the default, which is no.

#### Ignore missing or incomplete arch fields in the build script, (passing `-A` to `makepkg` during package building)
Create a key called `ignore_arch` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
ignore_arch
```

#### Set packages that are to be treated as development packages
List the names of the packages in the section `[devel_packages]`.

Example:
```ini
[devel_packages]
package_name1
package_name2
```

#### Specify a non-default folder to save `aurman` cache files
Create a key called `cache_dir` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
cache_dir=/tmp/aurman
```

#### Specify the timeout for AUR RPC and archlinux.org feed requests (in seconds) (default is 5)
Create a key called `aur_timeout` in the section `[miscellaneous]`.

Example:
```ini
[miscellaneous]
aur_timeout=10
```

#### Set interval in which to call `sudo -v` (sudo loop) (in seconds) (default is 120)
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

Explanation: https://git.archlinux.org/pacman.git/commit/?id=90e3e026d1236ad89c142b427d7eeb842bbb7ff4

`aurman` will use `--ask=4` if this config option is set.
You will not have to confirm things like the installation of packages or the removal of conflicting packages again.
"Again" - meaning again for `pacman`.
You will still see the overview of `aurman`, which only predicts what will happen, and you will have to confirm unless `--noconfirm` was set.
To be clear: `aurman` only predicts what will happen in every case.
When using `--ask=4`, it may be possible that a conflict will not be detected by `aurman`. Hence, using `--ask=4` may lead
to unintended removal of package(s).
All in all it comes down to: "redundant" confirmations of actions (less prone to errors)
or "not redundant" confirmations of actions (more prone to errors).


## Features

  - Threaded sudo loop in the background so you only have to enter your password once.
  - Reliable dependency resolving.
  - Conflict detection.
  - Split package support.
  - Development package support.
  - Distinction between explicitly and implicitly installed packages.
  - Lets you see and edit all needed PKGBUILDs before starting AUR package building.
  - Fetching of needed PGP keys for package building.
  - Pacman --search for repo and AUR packages (results sorted by popularity).
  - Search function supports regex for searching the AUR the first span of at least two consecutive non-regex
  characters being used. These results will be filtered by the regex expression afterwards.
  - Differentiate between the sources of packages in case of identical names in different known repos and/or the AUR.
  - Show unread news from `archlinux.org`.
  - Be notified about new locations of packages, e.g. moving from AUR to a known repository.
  - Be notified about orphans after installation of packages has finished.

## Dependency solving description including benchmarks
https://github.com/polygamma/aurman/wiki/Description-of-the-aurman-dependency-solving

## Using aurman just as a dependency solver
In order to discover available updates, search for potential packages to install and more, it is useful to get machine-readable descriptions of the potential sync/install/update transactions aurman can propose.

`aurmansolver [options]` answers this need, by providing a json *description* of the equivalent `aurman [options]` transaction, but without carrying out any changes.

One example use is with `-Su`, in order to list packages which have updates available.

See https://github.com/polygamma/aurman/wiki/Using-aurman-as-dependency-solver for a detailed explanation

## FAQ
#### Question
`aurman` wants to remove packages that should not be removed - what's the matter?

#### Answer
Please check if the problem arises because `aurman` has assumed `.so` dependencies to be unfulfilled.
*E.g.* `libavcodec.so=57-64` which requires a specific version of the mentioned `.so`.
This may be the case because a providing AUR package only lists `libavcodec.so` as being provided
without specifying the version. Hence `aurman` cannot be sure if the version will match,
since this can only be known after building the package, and thus assumes that the dependency is not fulfilled.
You may change this behavior by yielding `--optimistic_versioning` via the commandline.
Now, `aurman` (optimistically!) assumes the dependency will be fulfilled.
However, you should make sure that the version in the built package is going to be the needed one,
otherwise the optimism was misplaced and `aurman`'s behavior when installing the packages will be undefined.

This behavior may also occur when there are no `.so` dependencies involved.
Check if the dependencies are *really* fulfilled.
If they are not, because you forced installations of packages with `pacman -d`, this behavior is explicitly wanted.
It warns you about broken package dependencies in the system.
To remove this output of `aurman` you will have to fulfill the dependencies.


> **Notice**: `aurman` will **never** remove packages on its own. `aurman` just **predicts** what will happen.

#### Question
How do I change the editor used by `aurman` for editing PKGBUILDs etc.?

#### Answer
`aurman` uses the environment variables `VISUAL` and `EDITOR`, hence you will have to change these variables.

If `VISUAL` is set, `aurman` uses this,

else if `EDITOR` is set, `aurman` uses this,

else `aurman` resorts to `/usr/bin/nano`.

#### Question
How to install packages whose names are saved in a file with `aurman`?

#### Answer
`aurman` does not implement this functionality. Instead you may use standard shell command substitution.
*e.g.*: `aurman -S $(cat ~/packages_names.txt)`.

#### Question
Does `aurman` support ignoring packages and groups via `pacman.conf`?

#### Answer
Yes.

#### Question
I get a `UnicodeEncodeError` or a `UnicodeDecodeError` when executing `aurman` - how to fix it?

#### Answer
See: https://github.com/polygamma/aurman/issues/88.

#### Question
I am using `Arch ARM` and I am getting `expac` errors when executing `aurman`, what to do?

#### Answer
see: https://github.com/polygamma/aurman/issues/200

tl;dr - install the latest `expac-git` version from the AUR and everything works

#### Question
How to achieve `full batch interaction` with `aurman`?

#### Answer
Use `--do_everything` and `--ask` via the `aurman` config file.

`--do_everything` for `2*` and `--ask` for `3*` as listed [here](https://wiki.archlinux.org/index.php/AUR_helpers#Active)

But there are downsides to this. See the description of `--do_everything` [here](https://github.com/polygamma/aurman#options-for---sync-or--s-exclusive-to-aurman)
and the description of `--ask` [here](https://github.com/polygamma/aurman#make-use-of-the-undocumented---ask-flag-of-pacman).

#### Question
If I want to run `aurman` from scripts, which settings should I use?

#### Answer
See the answer to the previous question.

Also use the options `--noedit`, `--pgp_fetch`, `--skip_news`, `--noconfirm` and `--skip_new_locations`.

## Screenshots

![](https://i.imgur.com/Q80aK61.png)
![](https://i.imgur.com/37SGzAe.png)
![](https://i.imgur.com/Ou3S9m8.png)
![](https://i.imgur.com/7v24k19.png)
![](https://i.imgur.com/8Xu9oHc.png)
