import logging
import os
import sys
from copy import deepcopy
from subprocess import run, DEVNULL
from sys import argv, stdout
from typing import List, Tuple, Dict

from aurman.bash_completion import possible_completions
from aurman.classes import System, Package, PossibleTypes
from aurman.coloring import aurman_error, aurman_status, aurman_note, Colors
from aurman.help_printing import aurman_help
from aurman.own_exceptions import InvalidInput
from aurman.parse_args import PacmanOperations, parse_pacman_args, PacmanArgs
from aurman.parsing_config import read_config, packages_from_other_sources, AurmanConfig
from aurman.utilities import acquire_sudo, version_comparison, search_and_print, ask_user, strip_versioning_from_name
from aurman.wrappers import pacman, expac, pacman_conf

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
        aurman_note(expac("-Q", ("v",), ("aurman-git", "aurman"))[0])
    else:
        print(expac("-Q", ("v",), ("aurman-git", "aurman"))[0])
    sys.exit(0)


def redirect_pacman(pacman_args: 'PacmanArgs', args: List[str]) -> None:
    """
    redirects the user input without changes to pacman
    :param pacman_args: the parsed args
    :param args: the args unparsed
    """
    try:
        if pacman_args.operation in [
            PacmanOperations.UPGRADE, PacmanOperations.REMOVE, PacmanOperations.DATABASE, PacmanOperations.FILES
        ]:
            run("sudo pacman {}".format(" ".join(["'{}'".format(arg) for arg in args])), shell=True)
        else:
            run("pacman {}".format(" ".join(["'{}'".format(arg) for arg in args])), shell=True)
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
        not_remove.extend(pacman_conf("HoldPkg"))
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
        pacman(str(pacman_args), False, sudo=True)

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
                if run(
                        "rm -rf {}".format(Package.cache_dir), shell=True, stdout=DEVNULL, stderr=DEVNULL
                ).returncode != 0:
                    aurman_error(
                        "Directory {} could not be deleted".format(Colors.BOLD(Colors.LIGHT_MAGENTA(Package.cache_dir)))
                    )
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
                expac_returns = expac("-Q -1", ("e", "n"), ())
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
                            dir_to_delete = os.path.join(Package.cache_dir, thing)
                            if run(
                                    "rm -rf {}".format(dir_to_delete), shell=True, stdout=DEVNULL, stderr=DEVNULL
                            ).returncode != 0:
                                aurman_error(
                                    "Directory {} could not be deleted".format(
                                        Colors.BOLD(Colors.LIGHT_MAGENTA(dir_to_delete))
                                    )
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
                                "git clean -ffdx", shell=True, stdout=DEVNULL, stderr=DEVNULL, cwd=dir_to_clean
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

    # start search
    try:
        search_and_print(packages_of_user_names, installed_system, str(pacman_args), repo, aur)
    except InvalidInput:
        sys.exit(1)

    sys.exit(0)


def get_groups_to_install(packages_of_user_names: List[str], aur: bool) -> List[str]:
    """
    gets groups the user wants to install
    :param packages_of_user_names: the targets entered by the user
    :param aur: if --aur
    :return: the groups entered by the user
    """
    groups_chosen = []
    if not aur:
        groups = pacman("-Sg", True, sudo=False)
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
        pacman(str(pacman_args_copy), False)
    except InvalidInput:
        sys.exit(1)

    return sudo_acquired, pacman_called


def process(args):
    import aurman.aur_utilities

    readconfig()
    check_privileges()
    pacman_args = parse_parameters(args)

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
    packages_of_user_names = list(set(pacman_args.targets))  # targets of the aurman command without duplicates
    sysupgrade = pacman_args.sysupgrade  # if -u or --sysupgrade
    sysupgrade_force = sysupgrade and not isinstance(sysupgrade, bool)  # if -u -u or --sysupgrade --sysupgrade
    needed = pacman_args.needed  # if --needed
    noedit = pacman_args.noedit  # if --noedit
    always_edit = pacman_args.always_edit  # if --always_edit
    show_changes = pacman_args.show_changes \
                   or 'miscellaneous' in AurmanConfig.aurman_config \
                   and 'show_changes' in AurmanConfig.aurman_config['miscellaneous']  # if --show_changes
    devel = pacman_args.devel  # if --devel
    only_unfulfilled_deps = not pacman_args.deep_search  # if not --deep_search
    pgp_fetch = pacman_args.pgp_fetch  # if --pgp_fetch
    noconfirm = pacman_args.noconfirm  # if --noconfirm
    search = pacman_args.search  # if --search
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
        aurman.utilities.SudoLoop.timeout = int(AurmanConfig.aurman_config['miscellaneous']['sudo_timeout'])

    # change aur domain if configured by the user
    if pacman_args.domain:
        aurman.aur_utilities.aur_domain = pacman_args.domain[0]

    # change aur rpc timeout if set by the user
    if 'miscellaneous' in AurmanConfig.aurman_config \
            and 'aur_timeout' in AurmanConfig.aurman_config['miscellaneous']:
        aurman.aur_utilities.aur_timeout = int(AurmanConfig.aurman_config['miscellaneous']['aur_timeout'])

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

    # groups are for pacman
    # removes found groups from packages_of_user_names
    groups_chosen = get_groups_to_install(packages_of_user_names, aur)

    # pacman call in the beginning of the routine
    if not aur and \
            (sysupgrade and (not do_everything or pacman_args.refresh) or groups_chosen):
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
    packages_to_show = [package for package in installed_system.not_repo_not_aur_packages_list
                        if package.name not in concrete_no_notification_packages]

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
    if not repo:
        upstream_system.append_packages_by_name(packages_of_user_names)
        # fetch info for all installed aur packages, too
        names_of_installed_aur_packages = [package.name for package in installed_system.aur_packages_list]
        names_of_installed_aur_packages.extend([package.name for package in installed_system.devel_packages_list])
        upstream_system.append_packages_by_name(names_of_installed_aur_packages)

    # remove known repo packages in case of --aur
    if aur:
        for package in upstream_system.repo_packages_list:
            del upstream_system.all_packages_dict[package.name]
        upstream_system = System(list(upstream_system.all_packages_dict.values()))

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

    # if user entered --devel and not --repo, fetch all needed pkgbuilds etc. for the devel packages
    if devel and not repo:
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
                package.get_devel_version(ignore_arch)

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
        if not repo:
            installed_packages.extend([package for package in installed_system.aur_packages_list])
            installed_packages.extend([package for package in installed_system.devel_packages_list])
        if not aur:
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
            for possible_replacing_package in upstream_system.repo_packages_list:
                for replaces in possible_replacing_package.replaces:
                    replace_name = strip_versioning_from_name(replaces)
                    installed_to_replace = [
                        package for package in installed_system.provided_by(replaces) if package.name == replace_name
                    ]
                    if installed_to_replace:
                        assert len(installed_to_replace) == 1
                        package_to_replace = installed_to_replace[0]
                        # do not let packages replaces itself, e.g. mesa replaces "ati-dri" and provides "ati-dri"
                        if possible_replacing_package.name not in ignored_packages_names \
                                and package_to_replace.name not in ignored_packages_names \
                                and possible_replacing_package.name != package_to_replace.name:

                            replaces_dict[possible_replacing_package.name] = package_to_replace.name
                            if possible_replacing_package not in concrete_packages_to_install:
                                concrete_packages_to_install.append(possible_replacing_package)

                            if package_to_replace.name in upstream_system.all_packages_dict \
                                    and upstream_system.all_packages_dict[package_to_replace.name] \
                                    in concrete_packages_to_install:
                                concrete_packages_to_install.remove(
                                    upstream_system.all_packages_dict[package_to_replace.name]
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
    if not repo:
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

    args_for_explicit = str(pacman_args_copy)
    pacman_args_copy.asdeps = True
    pacman_args_copy.asexplicit = False
    args_for_dependency = str(pacman_args_copy)

    # calc chunks to install
    solution_packages_chunks = System.calc_install_chunks(chosen_solution)

    # install the chunks
    for package_chunk in solution_packages_chunks:
        # repo chunk
        if package_chunk[0].type_of is PossibleTypes.REPO_PACKAGE:
            # container for explicit repo deps
            as_explicit_container = set()
            for package in package_chunk:
                if package.name in sanitized_names \
                        and package.name not in sanitized_not_to_be_removed \
                        and package.name not in replaces_dict \
                        or (package.name in installed_system.all_packages_dict
                            and installed_system.all_packages_dict[package.name].install_reason
                            == 'explicit') \
                        or (package.name in replaces_dict
                            and installed_system.all_packages_dict[replaces_dict[package.name]].install_reason
                            == 'explicit'):
                    as_explicit_container.add(package.name)

            pacman_args_copy = deepcopy(pacman_args)
            pacman_args_copy.targets = [
                package.name for package in package_chunk if package.name not in repo_packages_dict
            ]

            pacman_args_copy.targets.extend(["{}/".format(repo_packages_dict[package.name]) + package.name
                                             for package in package_chunk if package.name in repo_packages_dict])
            pacman_args_copy.asdeps = True
            pacman_args_copy.asexplicit = False
            try:
                pacman(str(pacman_args_copy), False, use_ask=use_ask)
            except InvalidInput:
                sys.exit(1)

            if as_explicit_container:
                pacman("-D --asexplicit {}".format(" ".join(as_explicit_container)), True, sudo=True)
        # aur chunks always consist of one package
        else:
            package = package_chunk[0]
            try:
                package.build(ignore_arch, rebuild)
                if package.name in sanitized_names \
                        and package.name not in sanitized_not_to_be_removed \
                        and package.name not in replaces_dict \
                        or (package.name in installed_system.all_packages_dict
                            and installed_system.all_packages_dict[package.name].install_reason
                            == 'explicit') \
                        or (package.name in replaces_dict
                            and installed_system.all_packages_dict[replaces_dict[package.name]].install_reason
                            == 'explicit'):

                    package.install(args_for_explicit, use_ask=use_ask)
                else:
                    package.install(args_for_dependency, use_ask=use_ask)
            except InvalidInput:
                sys.exit(1)


def main():
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
