import fnmatch
import json
import logging
import os
import re
import sys
from copy import deepcopy
from datetime import datetime
from subprocess import run, DEVNULL
from sys import argv, stdout
from typing import List, Tuple, Dict, Set

import feedparser
import requests
from dateutil.tz import tzlocal
from pycman.config import PacmanConfig

from aurman.aur_utilities import get_aur_info, AurVars
from aurman.bash_completion import possible_completions
from aurman.classes import System, Package, PossibleTypes
from aurman.coloring import aurman_error, aurman_status, aurman_note, Colors
from aurman.help_printing import aurman_help
from aurman.own_exceptions import InvalidInput, ConnectionProblem
from aurman.parse_args import PacmanOperations, parse_pacman_args, PacmanArgs
from aurman.parsing_config import read_config, packages_from_other_sources, AurmanConfig
from aurman.utilities import acquire_sudo, version_comparison, search_and_print, ask_user, strip_versioning_from_name, \
    SudoLoop, SearchSortBy
from aurman.wrappers import pacman, expac

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(funcName)s - %(levelname)s - %(message)s')


def readconfig() -> None:
    """
    reads the aurman config and makes it available for the whole program
    """
    try:
        read_config()  # read config - available via AurmanConfig.aurman_config
    except InvalidInput:
        sys.exit(1)


def check_privileges() -> None:
    """
    checks the privileges and exists in case of aurman being executed with sudo
    """
    if os.getuid() == 0:
        aurman_error("Do not run aurman with sudo")
        sys.exit(1)


def parse_parameters(args: List[str]) -> 'PacmanArgs':
    """
    parses the parameters of the user
    :param args: the args to parse
    :return: the parsed args
    """
    try:
        return parse_pacman_args(args)
    except InvalidInput:
        aurman_note("aurman --help or aurman -h")
        sys.exit(1)


def show_help() -> None:
    """
    shows the help of aurman
    """
    # remove colors in case of not terminal
    if stdout.isatty():
        print(aurman_help)
    else:
        print(Colors.strip_colors(str(aurman_help)))
    sys.exit(0)


def show_version() -> None:
    """
    shows the version of aurman
    """
    # remove colors in case of not terminal
    if stdout.isatty():
        aurman_note(expac("-Q", ["v"], ["aurman-git", "aurman"])[0])
    else:
        print(expac("-Q", ["v"], ["aurman-git", "aurman"])[0])
    sys.exit(0)


def redirect_pacman(pacman_args: 'PacmanArgs', args: List[str]) -> None:
    """
    redirects the user input without changes to pacman
    :param pacman_args: the parsed args
    :param args: the args unparsed
    """
    try:
        cmd = ["pacman"]
        if pacman_args.operation in [
            PacmanOperations.UPGRADE, PacmanOperations.REMOVE, PacmanOperations.DATABASE, PacmanOperations.FILES
        ]:
            cmd = ["sudo", "pacman"]
        run(cmd + args)
    except InvalidInput:
        sys.exit(1)

    sys.exit(0)


def get_holdpkgs(pacman_args: 'PacmanArgs') -> List[str]:
    """
    returns the holdpkgs from the command line and pacman.conf
    :param pacman_args: the parsed args
    :return: the holdpkgs names
    """
    not_remove = pacman_args.holdpkg  # list containing the specified packages for --holdpkg
    # if --holdpkg_conf append holdpkg from pacman.conf
    if pacman_args.holdpkg_conf:
        not_remove.extend(PacmanConfig(conf="/etc/pacman.conf").options['HoldPkg'])
    # remove duplicates
    return list(set(not_remove))


def get_keyserver(pacman_args: 'PacmanArgs') -> str:
    if pacman_args.keyserver:
        keyserver = pacman_args.keyserver[0]
    else:
        keyserver = None

    if keyserver is None \
            and 'miscellaneous' in AurmanConfig.aurman_config \
            and 'keyserver' in AurmanConfig.aurman_config['miscellaneous']:
        keyserver = AurmanConfig.aurman_config['miscellaneous']['keyserver']

    return keyserver


def clean_cache(pacman_args: 'PacmanArgs', aur: bool, repo: bool, clean_force: bool, noconfirm: bool) -> None:
    """
    cleans the cache of pacman and aurman
    :param pacman_args: the parsed args
    :param aur: if --aur
    :param repo: if --aur
    :param clean_force: if -cc
    :param noconfirm: if --noconfirm
    """
    if not aur:
        pacman(pacman_args.args_as_list(), False, sudo=True)

    if not repo:
        if not os.path.isdir(Package.cache_dir):
            aurman_error(
                "Cache directory {} not found.".format(Colors.BOLD(Colors.LIGHT_MAGENTA(Package.cache_dir)))
            )
            sys.exit(1)

        aurman_note("Cache directory: {}".format(Colors.BOLD(Colors.LIGHT_MAGENTA(Package.cache_dir))))

        if clean_force:
            if noconfirm or \
                    ask_user(
                        "Do you want to remove {} from cache?".format(Colors.BOLD(Colors.LIGHT_MAGENTA("all files"))),
                        False
                    ):
                aurman_status("Deleting cache dir...")
                if run(["rm", "-rf", Package.cache_dir], stdout=DEVNULL).returncode != 0:
                    aurman_error("Deleting directory {} failed".format(Package.cache_dir))
                    sys.exit(1)
        else:
            if noconfirm or \
                    ask_user(
                        "Do you want to remove {} clones from cache?".format(
                            Colors.BOLD(Colors.LIGHT_MAGENTA("all uninstalled"))
                        ),
                        False
                    ):
                aurman_status("Deleting uninstalled clones from cache...")

                # if pkgbase not available, the name of the package is the base
                expac_returns = expac("-Q1", ["e", "n"], [])
                dirs_to_not_delete = set()
                for expac_return in expac_returns:
                    pkgbase = expac_return.split("?!")[0]
                    if pkgbase == "(null)":
                        dirs_to_not_delete.add(expac_return.split("?!")[1])
                    else:
                        dirs_to_not_delete.add(pkgbase)

                for thing in os.listdir(Package.cache_dir):
                    if os.path.isdir(os.path.join(Package.cache_dir, thing)):
                        if thing not in dirs_to_not_delete:
                            if run(
                                    ["rm", "-rf", os.path.join(Package.cache_dir, thing)], stdout=DEVNULL
                            ).returncode != 0:
                                aurman_error(
                                    "Deleting directory {} failed".format(os.path.join(Package.cache_dir, thing))
                                )
                                sys.exit(1)

            if not noconfirm and \
                    ask_user(
                        "Do you want to remove {} from cache? ({})".format(
                            Colors.BOLD(Colors.LIGHT_MAGENTA("all untracked git files")),
                            Colors.BOLD(Colors.LIGHT_MAGENTA("even from installed packages"))
                        ),
                        False
                    ):
                aurman_status("Deleting untracked git files from cache...")
                for thing in os.listdir(Package.cache_dir):
                    if os.path.isdir(os.path.join(Package.cache_dir, thing)):
                        dir_to_clean = os.path.join(Package.cache_dir, thing)
                        if run(
                                ["git", "clean", "-ffdx"], stdout=DEVNULL, stderr=DEVNULL, cwd=dir_to_clean
                        ).returncode != 0:
                            aurman_error(
                                "Directory {} could not be cleaned".format(
                                    Colors.BOLD(Colors.LIGHT_MAGENTA(dir_to_clean))
                                )
                            )
                            sys.exit(1)

    sys.exit(0)


def search_packages(pacman_args: 'PacmanArgs', packages_of_user_names: List[str], repo: bool, aur: bool) -> None:
    """
    searches for packages, so -Ss
    :param pacman_args: the parsed args
    :param packages_of_user_names: the targets to search for
    :param repo: if --repo
    :param aur: if --aur
    """
    # we only need the installed system for aur queries
    if not repo:
        try:
            installed_system = System(System.get_installed_packages())
        except InvalidInput:
            sys.exit(1)
    else:
        installed_system = None

    sort_by: SearchSortBy = None
    if pacman_args.sort_by_name:
        sort_by = SearchSortBy.NAME
    if pacman_args.sort_by_votes:
        if sort_by is not None:
            aurman_error("You cannot sort by multiple criteria at the same time")
            sys.exit(1)
        sort_by = SearchSortBy.VOTES
    if pacman_args.sort_by_popularity:
        if sort_by is not None:
            aurman_error("You cannot sort by multiple criteria at the same time")
            sys.exit(1)
        sort_by = SearchSortBy.POPULARITY

    # start search
    try:
        search_and_print(packages_of_user_names, installed_system, pacman_args, repo, aur, sort_by)
    except InvalidInput:
        sys.exit(1)

    sys.exit(0)


def show_packages_info(pacman_args: 'PacmanArgs', packages_of_user_names: List[str]) -> None:
    """
    shows the information of packages, just as pacman -Si
    :param pacman_args:             the parsed args
    :param packages_of_user_names:  the targets to show the information of
    """
    # pacman output
    run(["pacman"] + pacman_args.args_as_list(), stderr=DEVNULL)

    # output for aur packages
    for package_dict in get_aur_info(packages_of_user_names):
        for key, value in package_dict.items():
            if type(value) is list:
                value = '  '.join(value)
            elif key in ["OutOfDate", "FirstSubmitted", "LastModified"] and value is not None:
                value = datetime.fromtimestamp(value).replace(tzinfo=tzlocal()).strftime('%c')
            print("{}{} {}".format(Colors.BOLD(key.ljust(16)), Colors.BOLD(':'), value))
        print()

    sys.exit(0)


def get_groups_to_install(packages_of_user_names: List[str]) -> List[str]:
    """
    gets groups the user wants to install
    :param packages_of_user_names: the targets entered by the user
    :return: the groups entered by the user
    """
    groups_chosen = []
    groups = pacman(["-Sg"], True, sudo=False)
    for name in packages_of_user_names[:]:
        if name in groups:
            groups_chosen.append(name)
            # groups entered by the user must not be treated as packages
            packages_of_user_names.remove(name)

    return groups_chosen


def pacman_beginning_routine(pacman_args: 'PacmanArgs', groups_chosen: List[str], sudo_acquired: bool,
                             do_everything: bool) -> Tuple[bool, bool]:
    if not sudo_acquired:
        acquire_sudo()
        sudo_acquired = True
    pacman_called = True
    pacman_args_copy = deepcopy(pacman_args)
    pacman_args_copy.targets = groups_chosen
    # aurman handles the update
    if do_everything:
        pacman_args_copy.sysupgrade = False
    # ignore packages from other sources for sysupgrade
    try:
        packages_from_other_sources_ret = packages_from_other_sources()
    except InvalidInput:
        sys.exit(1)
    names_to_ignore = packages_from_other_sources_ret[0]
    for name_to_ignore in packages_from_other_sources_ret[1]:
        names_to_ignore.add(name_to_ignore)
    for already_ignored in pacman_args_copy.ignore:
        names_to_ignore |= set(already_ignored.split(","))
    if names_to_ignore:
        pacman_args_copy.ignore = [",".join(names_to_ignore)]
    try:
        pacman(pacman_args_copy.args_as_list(), False)
    except InvalidInput:
        sys.exit(1)

    return sudo_acquired, pacman_called


def show_unread_news():
    """
    Shows unread news from archlinux.org
    """
    # load list of already seen news
    try:
        os.makedirs(Package.cache_dir, mode=0o700, exist_ok=True)
    except OSError:
        logging.error("Creating cache dir {} failed".format(Package.cache_dir))
        raise InvalidInput("Creating cache dir {} failed".format(Package.cache_dir))

    seen_ids_file = os.path.join(Package.cache_dir, "seen_news_ids")
    if not os.path.isfile(seen_ids_file):
        open(seen_ids_file, 'a').close()

    with open(seen_ids_file, 'r') as seenidsfile:
        seen_ids: Set[str] = set([line for line in seenidsfile.read().strip().splitlines()])

    # fetch current news
    try:
        news_as_string: str = requests.get("https://www.archlinux.org/feeds/news/", timeout=AurVars.aur_timeout).text
    except requests.exceptions.RequestException:
        logging.error("Connection problem while requesting archlinux.org feed", exc_info=True)
        raise ConnectionProblem("Connection problem while requesting archlinux.org feed")

    # filter unseen news
    news_to_show = list(reversed(list(filter(
        lambda entry: entry['id'] not in seen_ids, feedparser.parse(news_as_string).entries
    ))))

    # if no unread news, return
    if not news_to_show:
        return

    # show unseen news
    for entry in news_to_show:
        aurman_note(
            "{} [{}]".format(Colors.BOLD(Colors.LIGHT_MAGENTA(entry['title'])), entry['published'])
        )
        print(re.sub('<[^<]+?>', '', entry['summary']) + '\n')

    if ask_user("Have you read the {} unread article(s) from archlinux.org?".format(
            Colors.BOLD(Colors.LIGHT_MAGENTA(len(news_to_show)))
    ), False):
        with open(seen_ids_file, 'a') as seenidsfile:
            seenidsfile.write('\n'.join([entry['id'] for entry in news_to_show]) + '\n')
    else:
        logging.error("User did not read the unseen news, but wanted to install packages on the system")
        raise InvalidInput("User did not read the unseen news, but wanted to install packages on the system")


def show_changed_package_repos(installed_system: 'System', upstream_system: 'System'):
    """
    Shows changed places of installed packages

    :param installed_system:    The installed system
    :param upstream_system:     The system containing the known upstream packages
    """
    # load list of the last known places of the packages
    known_places_file = os.path.join(Package.cache_dir, "known_package_places")
    if not os.path.isfile(known_places_file):
        # nothing to compare
        return

    with open(known_places_file, 'r') as f:
        # Dict.
        # Keys: names of packages, values: tuple
        #   Every tuple contains three items:
        #       1: bool: known in repo or aur
        #       2: bool: known in repo
        #       3: str:  if known in repo, name of repo
        known_package_places: Dict[str, Tuple[bool, bool, str]] = json.loads(f.read())

    # List containing the messages to print for the user.
    # Every tuple contains the name of the package, the old place and the new place
    packages_with_changes: List[Tuple[str, str, str]] = []
    for package_name, package in installed_system.all_packages_dict.items():
        if package_name not in known_package_places:
            continue

        old_package_information = known_package_places[package_name]

        if package.type_of is PossibleTypes.PACKAGE_NOT_REPO_NOT_AUR:
            if not old_package_information[0]:
                continue

            if old_package_information[1]:
                packages_with_changes.append((
                    package_name,
                    "{} repo".format(Colors.BOLD(Colors.LIGHT_MAGENTA(old_package_information[2]))),
                    Colors.BOLD(Colors.LIGHT_MAGENTA("not known"))
                ))
            else:
                packages_with_changes.append((
                    package_name,
                    Colors.BOLD(Colors.LIGHT_MAGENTA("AUR")),
                    Colors.BOLD(Colors.LIGHT_MAGENTA("not known"))
                ))

            continue

        upstream_package = upstream_system.all_packages_dict[package_name]

        if package.type_of is PossibleTypes.REPO_PACKAGE:
            if old_package_information[1]:
                if old_package_information[2] == upstream_package.repo:
                    continue

                packages_with_changes.append((
                    package_name,
                    "{} repo".format(Colors.BOLD(Colors.LIGHT_MAGENTA(old_package_information[2]))),
                    "{} repo".format(Colors.BOLD(Colors.LIGHT_MAGENTA(upstream_package.repo)))
                ))
            elif not old_package_information[0]:
                packages_with_changes.append((
                    package_name,
                    Colors.BOLD(Colors.LIGHT_MAGENTA("not known")),
                    "{} repo".format(Colors.BOLD(Colors.LIGHT_MAGENTA(upstream_package.repo)))
                ))
            else:
                packages_with_changes.append((
                    package_name,
                    Colors.BOLD(Colors.LIGHT_MAGENTA("AUR")),
                    "{} repo".format(Colors.BOLD(Colors.LIGHT_MAGENTA(upstream_package.repo)))
                ))

            continue

        # AUR package
        if old_package_information[0] and not old_package_information[1]:
            continue

        if not old_package_information[0]:
            packages_with_changes.append((
                package_name,
                Colors.BOLD(Colors.LIGHT_MAGENTA("not known")),
                Colors.BOLD(Colors.LIGHT_MAGENTA("AUR"))
            ))
        else:
            packages_with_changes.append((
                package_name,
                "{} repo".format(Colors.BOLD(Colors.LIGHT_MAGENTA(old_package_information[2]))),
                Colors.BOLD(Colors.LIGHT_MAGENTA("AUR"))
            ))

    if not packages_with_changes:
        return

    max_name_length = max([len(name) for name in [entry[0] for entry in packages_with_changes]])
    max_old_place_length = max([len(old_place) for old_place in [entry[1] for entry in packages_with_changes]])

    aurman_status("the following installed packages are found at new locations")
    for new_place_info in packages_with_changes:
        aurman_note("{} moved from {} to {}".format(
            Colors.BOLD(Colors.LIGHT_MAGENTA(new_place_info[0].ljust(max_name_length))),
            new_place_info[1].ljust(max_old_place_length),
            new_place_info[2])
        )

    if not ask_user(
            "Do you acknowledge the {} of the mentioned packages?".format(
                Colors.BOLD(Colors.LIGHT_MAGENTA("new locations"))
            ), False
    ):
        logging.error("User did not read about the changed packages locations, "
                      "but wanted to install packages on the system")
        raise InvalidInput("User did not read about the changed packages locations, "
                           "but wanted to install packages on the system")


def save_packages_repos(installed_system: 'System', upstream_system: 'System'):
    """
    Saves the current places of the installed packages

    :param installed_system:    The installed system
    :param upstream_system:     The system containing the known upstream packages
    """
    try:
        os.makedirs(Package.cache_dir, mode=0o700, exist_ok=True)
    except OSError:
        logging.error("Creating cache dir {} failed".format(Package.cache_dir))
        raise InvalidInput("Creating cache dir {} failed".format(Package.cache_dir))

    known_places_file = os.path.join(Package.cache_dir, "known_package_places")
    to_dump = {}

    for package_name, package in installed_system.all_packages_dict.items():
        if package.type_of is PossibleTypes.PACKAGE_NOT_REPO_NOT_AUR:
            to_dump[package_name] = (False, False, "")
        elif package.type_of is PossibleTypes.REPO_PACKAGE:
            to_dump[package_name] = (True, True, upstream_system.all_packages_dict[package_name].repo)
        else:
            to_dump[package_name] = (True, False, "")

    with open(known_places_file, 'w') as f:
        f.write(json.dumps(to_dump))


def save_orphans():
    """
    saves the current orphans - pacman -Qtdq
    """
    try:
        os.makedirs(Package.cache_dir, mode=0o700, exist_ok=True)
    except OSError:
        logging.error("Creating cache dir {} failed".format(Package.cache_dir))
        raise InvalidInput("Creating cache dir {} failed".format(Package.cache_dir))

    with open(os.path.join(Package.cache_dir, "current_orphans"), 'w') as f:
        try:
            f.write('\n'.join(pacman(["-Qtdq"], True, sudo=False, log_error=False)))
        except InvalidInput:
            f.write('')


def show_orphans(upstream_system: 'System'):
    """
    shows new orphans to the user - pacman -Qtdq
    :param upstream_system:     System containing the known upstream packages
    """
    try:
        current_orphans = set(pacman(["-Qtdq"], True, sudo=False, log_error=False))
    except InvalidInput:
        current_orphans = set()
    with open(os.path.join(Package.cache_dir, "current_orphans"), 'r') as f:
        saved_orphans = set(f.read().strip().splitlines())

    orphans_to_show = current_orphans - saved_orphans
    if not orphans_to_show:
        return

    aurman_status("the following packages are now orphans")
    aurman_note(", ".join([upstream_system.repo_of_package(orphan) for orphan in orphans_to_show]))


def package_as_explicit(package: 'Package', installed_system: 'System',
                        asdeps: bool, asexplicit: bool, replaces_dict: Dict[str, str],
                        sanitized_names: Set[str]) -> bool:
    """
    Whether an package has to be installed explicitly or not

    :param package:                         the package to install
    :param installed_system:                the system containing the installed packages
    :param asdeps:                          if --asdeps
    :param asexplicit:                      if --asexplicit
    :param replaces_dict:                   the dict containing the package replacements
    :param sanitized_names:                 the names of the packages explicitly wanted by the user
    :return:                                True if to be installed explicitly, False otherwise
    """
    if asdeps:
        return False
    elif asexplicit:
        return True

    if package.name in installed_system.all_packages_dict:
        return installed_system.all_packages_dict[package.name].install_reason == 'explicit'

    if package.name in replaces_dict:
        return installed_system.all_packages_dict[replaces_dict[package.name]].install_reason == 'explicit'

    return package.name in sanitized_names


def group_by_function_sort_by_deps(packages_to_sort: List['Package'], key_function) -> List['Package']:
    """
    Groups packages by the given key_function and sorts the packages, so that dependencies come first

    :param packages_to_sort:    the packages to sort
    :param key_function:        the function to group the packages by
    :return:                    the grouped and sorted packages
    """
    packages_to_sort.sort(key=key_function)
    current_group = []
    packages_groups = [current_group]

    for package in packages_to_sort:
        if not current_group or key_function(package) == key_function(current_group[0]):
            current_group.append(package)
        else:
            current_group = [package]
            packages_groups.append(current_group)

    ordered_package_groups = []
    for package_group in packages_groups:
        for i in range(0, len(ordered_package_groups)):
            package_group_to_compare = ordered_package_groups[i]
            deps_to_check = []
            for package in package_group_to_compare:
                deps_to_check.extend(package.relevant_deps())

            current_system = System(package_group)
            for dep in deps_to_check:
                if current_system.provided_by(dep):
                    ordered_package_groups.insert(i, package_group)
                    break
            else:
                continue

            break

        else:
            ordered_package_groups.append(package_group)

    return_list = []
    for package_group in ordered_package_groups:
        return_list.extend(package_group)
    return return_list


def process(args):
    readconfig()
    check_privileges()
    pacman_args = parse_parameters(args)

    if pacman_args.color:
        if pacman_args.color[0] == "always":
            Colors.color = 1
        elif pacman_args.color[0] == "never":
            Colors.color = 2
        elif pacman_args.color[0] != "auto":
            aurman_error("invalid option '{}' for --color".format(pacman_args.color[0]))
            sys.exit(1)

    if pacman_args.operation is PacmanOperations.HELP:
        show_help()

    if pacman_args.operation is PacmanOperations.VERSION:
        show_version()

    # if not -S or --sync, just redirect to pacman
    if pacman_args.operation is not PacmanOperations.SYNC:
        redirect_pacman(pacman_args, args)

    # -S or --sync
    # parse arguments
    Package.optimistic_versioning = pacman_args.optimistic_versioning \
                                    or 'miscellaneous' in AurmanConfig.aurman_config \
                                    and 'optimistic_versioning' \
                                    in AurmanConfig.aurman_config['miscellaneous']  # if --optimistic_versioning
    Package.ignore_versioning = pacman_args.ignore_versioning \
                                or 'miscellaneous' in AurmanConfig.aurman_config \
                                and 'ignore_versioning' \
                                in AurmanConfig.aurman_config['miscellaneous']  # if --ignore_versioning
    packages_of_user_names = list(set(pacman_args.targets))  # targets of the aurman command without duplicates
    sysupgrade = pacman_args.sysupgrade  # if -u or --sysupgrade
    sysupgrade_force = sysupgrade and not isinstance(sysupgrade, bool)  # if -u -u or --sysupgrade --sysupgrade
    needed = pacman_args.needed  # if --needed
    noedit = pacman_args.noedit  # if --noedit
    always_edit = pacman_args.always_edit  # if --always_edit
    show_changes = pacman_args.show_changes \
                   or 'miscellaneous' in AurmanConfig.aurman_config \
                   and 'show_changes' in AurmanConfig.aurman_config['miscellaneous'] \
                   and not noedit  # if --show_changes
    devel = pacman_args.devel  # if --devel
    only_unfulfilled_deps = not pacman_args.deep_search  # if not --deep_search
    pgp_fetch = pacman_args.pgp_fetch  # if --pgp_fetch
    noconfirm = pacman_args.noconfirm  # if --noconfirm
    search = pacman_args.search  # if --search
    info = pacman_args.info  # if --info
    solution_way = pacman_args.solution_way \
                   or 'miscellaneous' in AurmanConfig.aurman_config \
                   and 'solution_way' in AurmanConfig.aurman_config['miscellaneous']  # if --solution_way
    do_everything = pacman_args.do_everything \
                    or 'miscellaneous' in AurmanConfig.aurman_config \
                    and 'do_everything' in AurmanConfig.aurman_config['miscellaneous']  # if --do_everything
    clean = pacman_args.clean  # if --clean
    rebuild = pacman_args.rebuild  # if --rebuild
    clean_force = clean and not isinstance(clean, bool)  # if --clean --clean
    aur = pacman_args.aur  # do only aur things
    repo = pacman_args.repo  # do only repo things
    asdeps = pacman_args.asdeps  # if --asdeps
    asexplicit = pacman_args.asexplicit  # if --asexplicit
    skip_news = pacman_args.skip_news  # if --skip_news
    skip_new_locations = pacman_args.skip_new_locations  # if --skip_new_locations
    devel_skip_deps = pacman_args.devel_skip_deps  # if --devel_skip_deps
    show_new_locations = not skip_new_locations and not ('miscellaneous' in AurmanConfig.aurman_config
                                                         and 'skip_new_locations' in AurmanConfig.aurman_config[
                                                             'miscellaneous'])
    use_ask = 'miscellaneous' in AurmanConfig.aurman_config \
              and 'use_ask' in AurmanConfig.aurman_config['miscellaneous']  # if to use --ask=4

    # if the default for showing changes of pkgbuilds etc. should be yes instead of no
    default_show_changes = 'miscellaneous' in AurmanConfig.aurman_config \
                           and 'default_show_changes' in AurmanConfig.aurman_config['miscellaneous']

    # if to pass -A to makepkg
    ignore_arch = 'miscellaneous' in AurmanConfig.aurman_config and \
                  'ignore_arch' in AurmanConfig.aurman_config['miscellaneous']

    # validity check for user arguments
    # unrecognized parameters
    if pacman_args.invalid_args:
        aurman_error("The following parameters are not recognized yet: {}".format(pacman_args.invalid_args))
        aurman_note("aurman --help or aurman -h")
        sys.exit(1)

    if noedit and show_changes:
        aurman_error("--noedit and --show_changes is not what you want")
        sys.exit(1)

    if noedit and always_edit:
        aurman_error("--noedit and --always_edit is not what you want")
        sys.exit(1)

    if repo and aur:
        aurman_error("--repo and --aur is not what you want")
        sys.exit(1)

    if asdeps and asexplicit:
        aurman_error("--asdeps and --asexplicit is not what you want")
        sys.exit(1)

    # do not allow -y without -u
    if pacman_args.refresh and not sysupgrade:
        aurman_error("-y without -u is not allowed!")
        sys.exit(1)

    # packages to not notify about being unknown in either repos or the aur
    # global
    no_notification_unknown_packages = 'miscellaneous' in AurmanConfig.aurman_config and \
                                       'no_notification_unknown_packages' in AurmanConfig.aurman_config['miscellaneous']
    # single packages
    if 'no_notification_unknown_packages' in AurmanConfig.aurman_config:
        concrete_no_notification_packages = set(
            [package_name for package_name in AurmanConfig.aurman_config['no_notification_unknown_packages']]
        )
    else:
        concrete_no_notification_packages = set()

    # disable sudo loop if configured by the user
    sudo_acquired = 'miscellaneous' in AurmanConfig.aurman_config \
                    and 'no_sudo_loop' in AurmanConfig.aurman_config['miscellaneous']
    pacman_called = False

    # get holdpkgs
    not_remove = get_holdpkgs(pacman_args)

    # set keyserver
    keyserver = get_keyserver(pacman_args)

    # set sudo timeout if configured by the user
    if 'miscellaneous' in AurmanConfig.aurman_config \
            and 'sudo_timeout' in AurmanConfig.aurman_config['miscellaneous']:
        SudoLoop.timeout = int(AurmanConfig.aurman_config['miscellaneous']['sudo_timeout'])

    # change aur domain if configured by the user
    if pacman_args.domain:
        AurVars.aur_domain = pacman_args.domain[0]

    # change aur rpc timeout if set by the user
    if 'miscellaneous' in AurmanConfig.aurman_config \
            and 'aur_timeout' in AurmanConfig.aurman_config['miscellaneous']:
        AurVars.aur_timeout = int(AurmanConfig.aurman_config['miscellaneous']['aur_timeout'])

    # set the folder to save `aurman` cache files
    if 'miscellaneous' in AurmanConfig.aurman_config \
            and 'cache_dir' in AurmanConfig.aurman_config['miscellaneous']:
        Package.cache_dir = AurmanConfig.aurman_config['miscellaneous']['cache_dir']

    # --- start actually executing things --- #

    # if user wants to --clean
    if clean:
        clean_cache(pacman_args, aur, repo, clean_force, noconfirm)

    # if user just wants to search
    if search:
        search_packages(pacman_args, packages_of_user_names, repo, aur)

    # if user just wants to see info of packages
    if info:
        show_packages_info(pacman_args, packages_of_user_names)

    # show unread news from archlinux.org
    if not skip_news and not ('miscellaneous' in AurmanConfig.aurman_config
                              and 'skip_news' in AurmanConfig.aurman_config['miscellaneous']):
        try:
            show_unread_news()
        except InvalidInput:
            sys.exit(1)

    # groups are for pacman
    # removes found groups from packages_of_user_names
    groups_chosen = get_groups_to_install(packages_of_user_names)

    # pacman call in the beginning of the routine
    if sysupgrade and (not do_everything or pacman_args.refresh) or groups_chosen:
        sudo_acquired, pacman_called = pacman_beginning_routine(
            pacman_args, groups_chosen, sudo_acquired, do_everything
        )

    # nothing to do for us - exit
    if not sysupgrade and not packages_of_user_names:
        sys.exit(0)

    # delete -u --sysupgrade -y --refresh from parsed args
    # not needed anymore
    pacman_args.sysupgrade = False
    pacman_args.refresh = False

    # one status message
    if pacman_called:
        aurman_status("initializing {}...".format(Colors.BOLD("aurman")), True)
    else:
        aurman_status("initializing {}...".format(Colors.BOLD("aurman")), False)

    # analyzing installed packages
    try:
        installed_system = System(System.get_installed_packages())
    except InvalidInput:
        sys.exit(1)

    # print unknown packages for the user
    packages_not_show_names = set()
    not_repo_not_aur_packages_names = [package.name for package in installed_system.not_repo_not_aur_packages_list]
    for possible_glob in concrete_no_notification_packages:
        packages_not_show_names |= set(fnmatch.filter(
            not_repo_not_aur_packages_names, possible_glob
        ))

    packages_to_show = [
        package for package in installed_system.not_repo_not_aur_packages_list
        if package.name not in packages_not_show_names
    ]

    if packages_to_show and not no_notification_unknown_packages:
        aurman_status("the following packages are neither in known repos nor in the aur")
        for package in packages_to_show:
            aurman_note("{}".format(Colors.BOLD(Colors.LIGHT_MAGENTA(package))))

    # fetching upstream repo packages...
    try:
        upstream_system = System(System.get_repo_packages())
    except InvalidInput:
        sys.exit(1)

    # fetching needed aur packages
    upstream_system.append_packages_by_name(packages_of_user_names)
    # fetch info for all installed aur packages, too
    names_of_installed_aur_packages = [package.name for package in installed_system.aur_packages_list]
    names_of_installed_aur_packages.extend([package.name for package in installed_system.devel_packages_list])
    upstream_system.append_packages_by_name(names_of_installed_aur_packages)

    # show changes of places of installed packages
    if show_new_locations:
        try:
            show_changed_package_repos(installed_system, upstream_system)
            save_packages_repos(installed_system, upstream_system)
        except InvalidInput:
            sys.exit(1)

    # needed for later usage of save_packages_repos
    upstream_system_copy = System(upstream_system.all_packages_dict.values())

    # save current orphans
    save_orphans()

    # sanitize user input
    try:
        sanitized_names = upstream_system.sanitize_user_input(packages_of_user_names)
        sanitized_not_to_be_removed = installed_system.sanitize_user_input(not_remove)
    except InvalidInput:
        sys.exit(1)

    # names to not be removed must be also known on the upstream system,
    # otherwise aurman solving cannot handle this case.
    for name in sanitized_not_to_be_removed:
        if name not in upstream_system.all_packages_dict:
            aurman_error(
                "Packages you want to be not removed must be aur or repo packages.\n   {} is not known.".format(
                    Colors.BOLD(Colors.LIGHT_MAGENTA(name))
                )
            )
            sys.exit(1)

    # for dep solving not to be removed has to be treated as wanted to install
    sanitized_names |= sanitized_not_to_be_removed

    # fetching ignored packages
    ignored_packages_names = Package.get_ignored_packages_names(
        pacman_args.ignore, pacman_args.ignoregroup, upstream_system, installed_system, do_everything
    )
    # explicitly typed in names will not be ignored
    ignored_packages_names -= sanitized_names

    # print ignored packages for the user
    for ignored_packages_name in ignored_packages_names:
        if ignored_packages_name in upstream_system.all_packages_dict:
            if ignored_packages_name in installed_system.all_packages_dict:
                aurman_note(
                    "{} {} package {}".format(
                        Colors.BOLD(Colors.LIGHT_MAGENTA("Ignoring")),
                        Colors.BOLD(Colors.LIGHT_CYAN("installed")),
                        Colors.BOLD(Colors.LIGHT_MAGENTA(ignored_packages_name))
                    )
                )

                upstream_system.all_packages_dict[ignored_packages_name] = installed_system.all_packages_dict[
                    ignored_packages_name
                ]
            else:
                aurman_note(
                    "{} {} package {}".format(
                        Colors.BOLD(Colors.LIGHT_MAGENTA("Ignoring")),
                        Colors.BOLD(Colors.LIGHT_BLUE("upstream ")),
                        Colors.BOLD(Colors.LIGHT_MAGENTA(ignored_packages_name))
                    )
                )

                del upstream_system.all_packages_dict[ignored_packages_name]
        elif ignored_packages_name in installed_system.all_packages_dict:
            aurman_note(
                "{} {} package {}".format(
                    Colors.BOLD(Colors.LIGHT_MAGENTA("Ignoring")),
                    Colors.BOLD(Colors.LIGHT_CYAN("installed")),
                    Colors.BOLD(Colors.LIGHT_MAGENTA(ignored_packages_name))
                )
            )

    # recreating upstream system
    if ignored_packages_names:
        upstream_system = System(list(upstream_system.all_packages_dict.values()))

    # if user entered --devel, fetch all needed pkgbuilds etc. for the devel packages
    if devel:
        if not devel_skip_deps:
            missing_deps_dict: Dict[str, List[str]] = {}
            for package in [
                package for package in upstream_system.devel_packages_list if package.name not in ignored_packages_names
            ]:
                for dep in package.relevant_deps():
                    if not installed_system.provided_by(dep):
                        current_missing_deps = missing_deps_dict.get(package.name, [])
                        if not current_missing_deps:
                            missing_deps_dict[package.name] = [dep]
                        else:
                            current_missing_deps.append(dep)

            if missing_deps_dict:
                aurman_error(
                    "There are unfulfilled dependencies of development packages.\n"
                    "   Please fulfill them first\n"
                    "   or use {}\n"
                    "   or do not use {}\n"
                    "   or use {} to ignore respective packages".format(
                        Colors.BOLD(Colors.LIGHT_MAGENTA("--devel_skip_deps")),
                        Colors.BOLD(Colors.LIGHT_MAGENTA("--devel")),
                        Colors.BOLD(Colors.LIGHT_MAGENTA("--ignore"))
                    )
                )

                for package_name in missing_deps_dict:
                    aurman_note("{} misses {}".format(
                        upstream_system.repo_of_package(package_name),
                        ", ".join([Colors.BOLD(Colors.LIGHT_MAGENTA(dep)) for dep in missing_deps_dict[package_name]])
                    ))

                sys.exit(1)

        aurman_status("looking for new pkgbuilds of devel packages and fetching them...")
        for package in upstream_system.devel_packages_list:
            if package.name not in ignored_packages_names:
                package.fetch_pkgbuild()
        try:
            for package in upstream_system.devel_packages_list:
                if package.name not in ignored_packages_names:
                    package.show_pkgbuild(noedit, show_changes, pgp_fetch, keyserver, always_edit, default_show_changes)
        except InvalidInput:
            sys.exit(1)
        for package in upstream_system.devel_packages_list:
            if package.name not in ignored_packages_names:
                package.get_devel_version(ignore_arch, devel_skip_deps)

    # checking which packages need to be installed
    if not needed:
        concrete_packages_to_install = [upstream_system.all_packages_dict[name] for name in sanitized_names]
    else:
        possible_packages = [upstream_system.all_packages_dict[name] for name in sanitized_names]
        concrete_packages_to_install = []
        for package in possible_packages:
            if package.name in installed_system.all_packages_dict:
                installed_package = installed_system.all_packages_dict[package.name]
                if not version_comparison(installed_package.version, "=", package.version):
                    concrete_packages_to_install.append(package)
            else:
                concrete_packages_to_install.append(package)

    # dict for package replacements.
    # replacing packages names as keys, packages names to be replaced as values
    replaces_dict: Dict[str, str] = {}

    # in case of sysupgrade fetch all installed packages, of which newer versions are available
    if sysupgrade:
        installed_packages = []
        installed_packages.extend([package for package in installed_system.aur_packages_list])
        installed_packages.extend([package for package in installed_system.devel_packages_list])
        installed_packages.extend([package for package in installed_system.repo_packages_list])
        for package in installed_packages:
            # must not be that we have not received the upstream information
            assert package.name in upstream_system.all_packages_dict
            upstream_package = upstream_system.all_packages_dict[package.name]
            # normal sysupgrade
            if not sysupgrade_force:
                if version_comparison(upstream_package.version, ">", package.version):
                    if upstream_package not in concrete_packages_to_install:
                        concrete_packages_to_install.append(upstream_package)
            # sysupgrade with downgrades
            else:
                if not version_comparison(upstream_package.version, "=", package.version):
                    if upstream_package not in concrete_packages_to_install:
                        concrete_packages_to_install.append(upstream_package)

        # fetch packages to replace
        if do_everything:
            known_repo_names = Package.get_known_repos()

            for possible_replacing_package in upstream_system.repo_packages_list:
                for replaces in possible_replacing_package.replaces:
                    replace_name = strip_versioning_from_name(replaces)
                    installed_to_replace = [
                        package for package in installed_system.provided_by(replaces) if package.name == replace_name
                    ]
                    if installed_to_replace:
                        assert len(installed_to_replace) == 1
                        package_to_replace = installed_to_replace[0]

                        not_ignored = possible_replacing_package.name not in ignored_packages_names \
                                      and package_to_replace.name not in ignored_packages_names

                        not_same_name = possible_replacing_package.name != package_to_replace.name

                        not_known_in_repo = package_to_replace.type_of is not PossibleTypes.REPO_PACKAGE

                        try:
                            repo_order_allows_replacing = known_repo_names.index(
                                possible_replacing_package.repo
                            ) <= known_repo_names.index(upstream_system.all_packages_dict[package_to_replace.name].repo)
                        except ValueError:
                            repo_order_allows_replacing = not_known_in_repo

                        # implement pacman logic to decide whether to replace or not
                        if not_ignored and not_same_name and (not_known_in_repo or repo_order_allows_replacing):

                            replaces_dict[possible_replacing_package.name] = package_to_replace.name
                            if possible_replacing_package not in concrete_packages_to_install:
                                concrete_packages_to_install.append(possible_replacing_package)

                            if package_to_replace.name in upstream_system.all_packages_dict \
                                    and upstream_system.all_packages_dict[package_to_replace.name] \
                                    in concrete_packages_to_install:
                                concrete_packages_to_install.remove(
                                    upstream_system.all_packages_dict[package_to_replace.name]
                                )

    # chunk and sort packages
    concrete_packages_to_install_repo = [package for package in concrete_packages_to_install
                                         if package.type_of is PossibleTypes.REPO_PACKAGE]
    concrete_packages_to_install_aur = [package for package in concrete_packages_to_install
                                        if package.type_of is not PossibleTypes.REPO_PACKAGE]

    # if not --rebuild, handle repo packages first
    if not rebuild:
        concrete_packages_to_install = group_by_function_sort_by_deps(
            concrete_packages_to_install_repo, lambda pkg: pkg.pkgbase
        ) + group_by_function_sort_by_deps(
            concrete_packages_to_install_aur, lambda pkg: pkg.pkgbase
        )
    # if --rebuild, aur packages may be in front of repo packages
    else:
        concrete_packages_to_install = group_by_function_sort_by_deps(
            concrete_packages_to_install_repo + concrete_packages_to_install_aur, lambda pkg: pkg.pkgbase
        )

    # start calculating solutions
    aurman_status("calculating solutions...")
    if only_unfulfilled_deps:
        if not rebuild:
            solutions = Package.dep_solving(concrete_packages_to_install, installed_system, upstream_system)
        # if --rebuild, assume that the packages to rebuild are not installed, to ensure to correct order of rebuilding
        else:
            installed_system_no_rebuild_packages = System(
                [
                    package for package in installed_system.all_packages_dict.values()
                    if package.name not in sanitized_names
                ]
            )
            solutions = Package.dep_solving(
                concrete_packages_to_install, installed_system_no_rebuild_packages, upstream_system
            )
    else:
        solutions = Package.dep_solving(concrete_packages_to_install, System(()), upstream_system)

    # validates the found solutions and lets the user choose one of them, if there is more than one valid solution
    try:
        chosen_solution = installed_system.validate_and_choose_solution(
            solutions, concrete_packages_to_install, upstream_system, not only_unfulfilled_deps, solution_way
        )
    except InvalidInput:
        aurman_error("we could not find a solution")
        # if not --deep_search
        if only_unfulfilled_deps:
            aurman_error("if you think that there should be one, rerun aurman with the --deep_search flag")
        sys.exit(1)

    # needed because deep_search ignores installed packages
    if not only_unfulfilled_deps:
        pacman_args.needed = True

    # solution contains no packages
    if not chosen_solution:
        aurman_note("nothing to do... everything is up to date")
        sys.exit(0)

    # show solution to the user
    try:
        installed_system.show_solution_differences_to_user(
            chosen_solution, upstream_system, noconfirm, not only_unfulfilled_deps, solution_way
        )
    except InvalidInput:
        sys.exit(1)

    # fetch pkgbuilds
    aurman_status("looking for new pkgbuilds and fetching them...")
    for package in chosen_solution:
        if package.type_of is PossibleTypes.REPO_PACKAGE \
                or devel and package.type_of is PossibleTypes.DEVEL_PACKAGE:
            continue
        package.fetch_pkgbuild()
    try:
        for package in chosen_solution:
            if package.type_of is PossibleTypes.REPO_PACKAGE \
                    or devel and package.type_of is PossibleTypes.DEVEL_PACKAGE:
                continue
            package.show_pkgbuild(noedit, show_changes, pgp_fetch, keyserver, always_edit, default_show_changes)
    except InvalidInput:
        sys.exit(1)

    # install packages
    if not sudo_acquired:
        acquire_sudo()
        sudo_acquired = True

    # repo packages to install from other sources
    repo_packages_dict = packages_from_other_sources()[1]

    # generate pacman args for the aur packages
    pacman_args_copy = deepcopy(pacman_args)
    pacman_args_copy.operation = PacmanOperations.UPGRADE
    pacman_args_copy.targets = []

    pacman_args_copy.asdeps = False
    pacman_args_copy.asexplicit = True
    args_for_explicit = pacman_args_copy.args_as_list()

    pacman_args_copy.asdeps = True
    pacman_args_copy.asexplicit = False
    args_for_dependency = pacman_args_copy.args_as_list()

    # calc chunks to install
    solution_packages_chunks = System.calc_install_chunks(chosen_solution)

    try:
        # install the chunks
        for package_chunk in solution_packages_chunks:
            # repo chunk
            if package_chunk[0].type_of is PossibleTypes.REPO_PACKAGE:
                # container for explicit repo deps
                as_explicit_container = set()
                for package in package_chunk:
                    if package_as_explicit(
                            package, installed_system, asdeps, asexplicit, replaces_dict, sanitized_names
                    ):
                        as_explicit_container.add(package.name)

                pacman_args_copy = deepcopy(pacman_args)
                pacman_args_copy.targets = [
                    package.name for package in package_chunk if package.name not in repo_packages_dict
                ]

                pacman_args_copy.targets.extend(["{}/".format(repo_packages_dict[package.name]) + package.name
                                                 for package in package_chunk if package.name in repo_packages_dict])
                pacman_args_copy.asdeps = True
                pacman_args_copy.asexplicit = False

                pacman(pacman_args_copy.args_as_list(), False, use_ask=use_ask)

                if as_explicit_container:
                    pacman(["-D", "--asexplicit"] + list(as_explicit_container), True, sudo=True)

            # aur chunks may consist of more than one package in case of split packages to be installed
            else:
                # no split packages, single package
                if len(package_chunk) == 1:
                    package = package_chunk[0]
                    package.build(ignore_arch, rebuild)
                    if package_as_explicit(
                            package, installed_system, asdeps, asexplicit, replaces_dict, sanitized_names
                    ):
                        package.install(args_for_explicit, use_ask=use_ask)
                    else:
                        package.install(args_for_dependency, use_ask=use_ask)
                # split packages, multiple packages
                else:
                    build_dir: str = None
                    args_as_list: List[str] = args_for_dependency[:]
                    if use_ask:
                        args_as_list = ["--ask=4"] + args_as_list

                    as_explicit_container = set()
                    for package in package_chunk:
                        # building only needed once
                        if build_dir is None:
                            package.build(ignore_arch, rebuild)
                        build_dir, current_install_file = package.install(args_for_dependency, do_not_execute=True)
                        args_as_list += [current_install_file]

                        if package_as_explicit(
                                package, installed_system, asdeps, asexplicit, replaces_dict, sanitized_names
                        ):
                            as_explicit_container.add(package.name)

                    pacman(args_as_list, False, dir_to_execute=build_dir)

                    if as_explicit_container:
                        pacman(["-D", "--asexplicit"] + list(as_explicit_container), True, sudo=True)

    except InvalidInput:
        show_orphans(upstream_system_copy)
        if show_new_locations:
            save_packages_repos(System(System.get_installed_packages()), upstream_system_copy)
        sys.exit(1)

    # show new orphans
    show_orphans(upstream_system_copy)

    # save current repos of installed packages
    if show_new_locations:
        save_packages_repos(System(System.get_installed_packages()), upstream_system_copy)


def main():
    from locale import setlocale, LC_ALL
    setlocale(LC_ALL, '')  # initialize locales because python doesn't

    try:
        # auto completion
        if len(argv) >= 2 and argv[1] == "--auto_complete":
            possible_completions()
            sys.exit(0)

        # normal call
        process(argv[1:])
    except (KeyboardInterrupt, PermissionError):
        sys.exit(1)
    except SystemExit as e:
        sys.exit(e)
    except:
        logging.error("", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
