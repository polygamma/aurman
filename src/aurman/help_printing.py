from typing import Any, List

from aurman.coloring import Colors


class HelpPoint:
    def __init__(self, head, children):
        self.head: Any = head
        self.children: List = children

    def __repr__(self):
        return "{}\n{}".format(Colors.BOLD(self.head), ''.join(["\n    {}".format(child) for child in self.children]))


class HelpOption:
    def __init__(self, names, description):
        self.names: List[str] = names
        self.description: str = description

    def __repr__(self):
        if self.description:
            return_beginning = ", ".join([Colors.LIGHT_GREEN(name) for name in self.names]).ljust(
                20 + 10 * len(self.names))
            return "{}:  {}".format(return_beginning, self.description)
        else:
            return "{}".format(", ".join([Colors.LIGHT_GREEN(name) for name in self.names]))


class Help:
    def __init__(self, points):
        self.points: List['HelpPoint'] = points

    def __repr__(self):
        return "\n\n".join([str(point) for point in self.points])


# aurman help
aurman_help = Help([])

# usage
usage_title = "Usage"
usage = "aurman <operation> [options] [targets]\n    see also https://www.archlinux.org/pacman/pacman.8.html"
aurman_help.points.append(HelpPoint(usage_title, (usage,)))

# description
description_title = "Description"
description = "aurman is meant as a {}. " \
              "All pacman operations are supported,\n    " \
              "but calling aurman with an operation besides " \
              "{} or {} will {}.".format(Colors.BOLD("pacman wrapper"),
                                         Colors.BOLD(Colors.LIGHT_GREEN("--sync")),
                                         Colors.BOLD(Colors.LIGHT_GREEN("-S")),
                                         Colors.BOLD("just pass the arguments to pacman"))
aurman_help.points.append(HelpPoint(description_title, (description,)))

# native pacman options
native = "the following native pacman options for " \
         "{} or {} will be forwarded to pacman".format(Colors.LIGHT_GREEN("--sync"), Colors.LIGHT_GREEN("-S"))
native_points = []
aurman_help.points.append(HelpPoint(native, native_points))

native_points.append(HelpOption(["-r", "--root"],
                                "Specify an alternative database location (a typical default is /var/lib/pacman)"))
native_points.append(HelpOption(["-v", "--verbose"],
                                "Output paths such as as the Root, Conf File, DB Path, Cache Dirs, etc."))
native_points.append(HelpOption(["--cachedir"],
                                "Specify an alternative package cache location "
                                "(a typical default is /var/cache/pacman/pkg)"))
native_points.append(HelpOption(["--color"],
                                "Specify when to enable coloring"))
native_points.append(HelpOption(["--debug"],
                                "Display debug messages"))
native_points.append(HelpOption(["--gpgdir"],
                                "Specify a directory of files used by GnuPG to verify package signatures "
                                "(default is /etc/pacman.d/gnupg)"))
native_points.append(HelpOption(["--hookdir"],
                                "Specify a alternative directory containing hook files "
                                "(default is /etc/pacman.d/hooks)"))
native_points.append(HelpOption(["--logfile"],
                                "Specify an alternate log file"))
native_points.append(HelpOption(["--noconfirm"],
                                "Bypass any and all 'Are you sure?' messages"))
native_points.append(HelpOption(["--confirm"],
                                "Cancels the effects of a previous --noconfirm"))
native_points.append(HelpOption(["--force"],
                                "Bypass file conflict checks and overwrite conflicting files"))
native_points.append(HelpOption(["--asdeps"],
                                "Install packages non-explicitly"))
native_points.append(HelpOption(["--asexplicit"],
                                "Install packages explicitly"))
native_points.append(HelpOption(["--needed"],
                                "Do not reinstall the targets that are already up-to-date"))
native_points.append(HelpOption(["--ignore"],
                                "Directs pacman to ignore upgrades of package even if there is one available"))
native_points.append(HelpOption(["--ignoregroup"],
                                "Directs pacman to ignore upgrades of all packages in group, "
                                "even if there is one available."))
native_points.append(HelpOption(["-s", "--search"],
                                "This will search each package in the sync databases for names or descriptions"))
native_points.append(HelpOption(["-u", "--sysupgrade"],
                                "Upgrades all packages that are out-of-date"))
native_points.append(HelpOption(["-y", "--refresh"],
                                "Download a fresh copy of the master package database from the server"))

# native pacman options for aurman
native_aurman = "the following native pacman options for " \
                "{} or {} will also be used by aurman for aur packages".format(Colors.LIGHT_GREEN("--sync"),
                                                                               Colors.LIGHT_GREEN("-S"))
native_aurman_points = []
aurman_help.points.append(HelpPoint(native_aurman, native_aurman_points))

native_aurman_points.append(HelpOption(["--noconfirm"],
                                       "Bypass any and all 'Are you sure?' messages"))
native_aurman_points.append(HelpOption(["--needed"],
                                       "Do not reinstall the targets that are already up-to-date"))
native_aurman_points.append(HelpOption(["--ignore"],
                                       "Directs aurman to ignore upgrades of package even if there is one available"))
native_aurman_points.append(HelpOption(["-s", "--search"],
                                       "This will search each package in the sync databases and aur "
                                       "for names or descriptions"))
native_aurman_points.append(HelpOption(["-u", "--sysupgrade"],
                                       "Upgrades all packages that are out-of-date"))

# aurman exclusive options
only_aurman = "aurman exclusive options for {} or {}".format(Colors.LIGHT_GREEN("--sync"), Colors.LIGHT_GREEN("-S"))
only_aurman_points = []
aurman_help.points.append(HelpPoint(only_aurman, only_aurman_points))

only_aurman_points.append(HelpOption(["--noedit"],
                                     "will not show changes of PKGBUILDs and .install files"))
only_aurman_points.append(HelpOption(["--devel"],
                                     "will fetch current development packages versions"))
only_aurman_points.append(HelpOption(["--deep_search"],
                                     "dependency solving will ignore currently "
                                     "fulfilled dependencies of your system"))
only_aurman_points.append(HelpOption(["--pgp_fetch"],
                                     "fetches needed pgp keys without asking the user"))
only_aurman_points.append(HelpOption(["--keyserver name"],
                                     "you may specify a keyserver to fetch the pgp keys from"))
only_aurman_points.append(HelpOption(["--aur"],
                                     "do things only for aur"))
only_aurman_points.append(HelpOption(["--repo"],
                                     "do things only for regular repos"))
only_aurman_points.append(HelpOption(["--domain name"],
                                     "change the base url for aur requests (https://aur.archlinux.org is the default)"))
only_aurman_points.append(HelpOption(["--solution_way"],
                                     "print the way of installing/removing packages"))
only_aurman_points.append(HelpOption(["--holdpkg name"],
                                     "specify packages which must not be removed - "
                                     "multiple packages are space separated"))
only_aurman_points.append(HelpOption(["--holdpkg_conf"],
                                     "append packages from the pacman.conf to"
                                     " {}".format(Colors.LIGHT_GREEN("--holdpkg"))))
