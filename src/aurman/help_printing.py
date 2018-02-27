from typing import Iterable, Any, List

from aurman.coloring import Colors


class HelpPoint:
    def __init__(self, head, children):
        self.head: Any = head
        self.children: Iterable = children

    def __repr__(self):
        return "{}{}".format(Colors.BOLD(self.head), ''.join(
            ["\n   {} {}".format(Colors.BOLD(Colors.LIGHT_CYAN("-")), child) for child in self.children]))


class HelpOption:
    def __init__(self, names, description):
        self.names: Iterable[str] = names
        self.description: str = description

    def __repr__(self):
        if self.description:
            return "{}: {}".format(", ".join([Colors.LIGHT_GREEN(name) for name in self.names]), self.description)
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
usage = "aurman < operation > [ options ] [ targets ] - see also https://www.archlinux.org/pacman/pacman.8.html"
aurman_help.points.append(HelpPoint(usage_title, (usage,)))

# description
description_title = "Description"
description = "aurman is meant as a {}. " \
              "All pacman operations are supported, " \
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

native_points.append(HelpOption(["-r", "--root"], ""))
native_points.append(HelpOption(["-v", "--verbose"], ""))
native_points.append(HelpOption(["--cachedir"], ""))
native_points.append(HelpOption(["--color"], ""))
native_points.append(HelpOption(["--debug"], ""))
native_points.append(HelpOption(["--gpgdir"], ""))
native_points.append(HelpOption(["--hookdir"], ""))
native_points.append(HelpOption(["--logfile"], ""))
native_points.append(HelpOption(["--noconfirm"], ""))
native_points.append(HelpOption(["--confirm"], ""))
native_points.append(HelpOption(["--force"], ""))
native_points.append(HelpOption(["--asdeps"], ""))
native_points.append(HelpOption(["--asexplicit"], ""))
native_points.append(HelpOption(["--needed"], ""))
native_points.append(HelpOption(["-s", "--search"], ""))
native_points.append(HelpOption(["-u", "--sysupgrade"], ""))
native_points.append(HelpOption(["-y", "--refresh"], ""))

# native pacman options for aurman
native_aurman = "the following native pacman options for " \
                "{} or {} will also be used by aurman for aur packages".format(Colors.LIGHT_GREEN("--sync"),
                                                                               Colors.LIGHT_GREEN("-S"))
native_aurman_points = []
aurman_help.points.append(HelpPoint(native_aurman, native_aurman_points))

native_aurman_points.append(HelpOption(["--noconfirm"], ""))
native_aurman_points.append(HelpOption(["--needed"], ""))
native_aurman_points.append(HelpOption(["-s", "--search"], ""))
native_aurman_points.append(HelpOption(["-u", "--sysupgrade"], ""))

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
