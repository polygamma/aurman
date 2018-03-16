import logging
import os
import sys
from copy import deepcopy
from subprocess import run, DEVNULL
from sys import argv, stdout

from pycman.config import PacmanConfig

from aurman.bash_completion import possible_completions
from aurman.classes import System, Package, PossibleTypes
from aurman.coloring import aurman_error, aurman_status, aurman_note, Colors
from aurman.help_printing import aurman_help
from aurman.own_exceptions import InvalidInput
from aurman.parse_args import PacmanOperations, parse_pacman_args
from aurman.parsing_config import read_config, packages_from_other_sources, AurmanConfig
from aurman.utilities import acquire_sudo, version_comparison, search_and_print, ask_user
from aurman.wrappers import pacman, expac

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(funcName)s - %(levelname)s - %(message)s')


def process(args):
    import aurman.aur_utilities

    sudo_acquired = False

    try:
        read_config()  # read config - available via AurmanConfig.aurman_config
    except InvalidInput:
        sys.exit(1)

    # parse parameters of user
    try:
        pacman_args = parse_pacman_args(args)
    except InvalidInput:
        aurman_note("aurman --help or aurman -h")
        sys.exit(1)

    # show help
    if pacman_args.operation is PacmanOperations.HELP:
        # remove colors in case of not terminal
        if stdout.isatty():
            print(aurman_help)
        else:
            print(Colors.strip_colors(str(aurman_help)))
        sys.exit(0)

    # show version
    if pacman_args.operation is PacmanOperations.VERSION:
        # remove colors in case of not terminal
        if stdout.isatty():
            aurman_note(expac("-Q", ("v",), ("aurman-git",))[0])
        else:
            print(expac("-Q", ("v",), ("aurman-git",))[0])
        sys.exit(0)

    # if not -S or --sync, just redirect to pacman
    if pacman_args.operation is not PacmanOperations.SYNC:
        try:
            if pacman_args.operation in [PacmanOperations.UPGRADE, PacmanOperations.REMOVE, PacmanOperations.DATABASE]:
                run("sudo pacman {}".format(" ".join(args)), shell=True)
            else:
                run("pacman {}".format(" ".join(args)), shell=True)
        except InvalidInput:
            sys.exit(1)

        sys.exit(0)

    # -S or --sync
    packages_of_user_names = list(set(pacman_args.targets))  # targets of the aurman command without duplicates
    sysupgrade = pacman_args.sysupgrade  # if -u or --sysupgrade
    sysupgrade_force = sysupgrade and not isinstance(sysupgrade, bool)  # if -u -u or --sysupgrade --sysupgrade
    needed = pacman_args.needed  # if --needed
    noedit = pacman_args.noedit  # if --noedit
    show_changes = pacman_args.show_changes  # if --show_changes
    devel = pacman_args.devel  # if --devel
    only_unfulfilled_deps = not pacman_args.deep_search  # if not --deep_search
    pgp_fetch = pacman_args.pgp_fetch  # if --pgp_fetch
    noconfirm = pacman_args.noconfirm  # if --noconfirm
    search = pacman_args.search  # list containing the specified strings for -s and --search
    solution_way = pacman_args.solution_way  # if --solution_way
    do_everything = pacman_args.do_everything  # if --do_everything
    clean = pacman_args.clean  # if --clean
    clean_force = clean and not isinstance(clean, bool)  # if --clean --clean

    not_remove = pacman_args.holdpkg  # list containing the specified packages for --holdpkg
    # if --holdpkg_conf append holdpkg from pacman.conf
    if pacman_args.holdpkg_conf:
        not_remove.extend(PacmanConfig(conf="/etc/pacman.conf").options['HoldPkg'])
    # remove duplicates
    not_remove = list(set(not_remove))

    if noedit and show_changes:
        aurman_error("--noedit and --show_changes is not what you want")
        sys.exit(1)

    aur = pacman_args.aur  # do only aur things
    repo = pacman_args.repo  # do only repo things
    if repo and aur:
        aurman_error("--repo and --aur is not what you want")
        sys.exit(1)

    if pacman_args.keyserver:
        keyserver = pacman_args.keyserver[0]
    else:
        keyserver = None

    if keyserver is None \
            and 'miscellaneous' in AurmanConfig.aurman_config \
            and 'keyserver' in AurmanConfig.aurman_config['miscellaneous']:
        keyserver = AurmanConfig.aurman_config['miscellaneous']['keyserver']

    if pacman_args.domain:
        aurman.aur_utilities.aur_domain = pacman_args.domain[0]

    # do not allow -y without -u
    if pacman_args.refresh and not sysupgrade:
        aurman_error("-y without -u is not allowed!")
        sys.exit(1)

    # unrecognized parameters
    if pacman_args.invalid_args:
        aurman_error("The following parameters are not recognized yet: {}".format(pacman_args.invalid_args))
        aurman_note("aurman --help or aurman -h")
        sys.exit(1)

    # if user wants to --clean
    if clean:
        if not aur:
            pacman(str(pacman_args), False, sudo=True)

        if not repo:
            if not os.path.isdir(Package.cache_dir):
                aurman_error("Cache directory {} not found."
                             "".format(Colors.BOLD(Colors.LIGHT_MAGENTA(Package.cache_dir))))
                sys.exit(1)

            aurman_note("Cache directory: {}".format(Colors.BOLD(Colors.LIGHT_MAGENTA(Package.cache_dir))))

            if clean_force:
                if ask_user("Do you want to remove {} from cache?"
                            "".format(Colors.BOLD(Colors.LIGHT_MAGENTA("all files"))), False):
                    aurman_status("Deleting cache dir...")
                    if run("rm -rf {}".format(Package.cache_dir), shell=True, stdout=DEVNULL,
                           stderr=DEVNULL).returncode != 0:
                        aurman_error("Directory {} could not be deleted"
                                     "".format(Colors.BOLD(Colors.LIGHT_MAGENTA(Package.cache_dir))))
                        sys.exit(1)
            else:
                if ask_user("Do you want to remove {} clones from cache?"
                            "".format(Colors.BOLD(Colors.LIGHT_MAGENTA("all uninstalled"))), False):
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
                                if run("rm -rf {}".format(dir_to_delete), shell=True, stdout=DEVNULL,
                                       stderr=DEVNULL).returncode != 0:
                                    aurman_error("Directory {} could not be deleted"
                                                 "".format(Colors.BOLD(Colors.LIGHT_MAGENTA(dir_to_delete))))
                                    sys.exit(1)

                if ask_user("Do you want to remove {} from cache? ({})"
                            "".format(Colors.BOLD(Colors.LIGHT_MAGENTA("all untracked git files")),
                                      Colors.BOLD(Colors.LIGHT_MAGENTA("even from installed packages"))), False):
                    aurman_status("Deleting untracked git files from cache...")
                    for thing in os.listdir(Package.cache_dir):
                        if os.path.isdir(os.path.join(Package.cache_dir, thing)):
                            dir_to_clean = os.path.join(Package.cache_dir, thing)
                            if run("git clean -ffdx"
                                   "", shell=True, stdout=DEVNULL, stderr=DEVNULL, cwd=dir_to_clean).returncode != 0:
                                aurman_error("Directory {} could not be cleaned"
                                             "".format(Colors.BOLD(Colors.LIGHT_MAGENTA(dir_to_clean))))
                                sys.exit(1)

        sys.exit(0)

    # if user just wants to search
    if search:
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
            search_and_print(search, installed_system, str(pacman_args), repo, aur)
        except InvalidInput:
            sys.exit(1)

        sys.exit(0)

    # groups are for pacman
    groups_chosen = []
    if not aur:
        groups = pacman("-Sg", True, sudo=False)
        for name in packages_of_user_names[:]:
            if name in groups:
                groups_chosen.append(name)
                packages_of_user_names.remove(name)

    # pacman call in the beginning of the routine
    if not aur \
            and (sysupgrade and (not do_everything or pacman_args.refresh) or groups_chosen):
        if not sudo_acquired:
            acquire_sudo()
            sudo_acquired = True
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

    # nothing to do for us
    if not sysupgrade and not packages_of_user_names:
        sys.exit(0)

    # delete -u --sysupgrade -y --refresh from parsed args
    # not needed anymore
    pacman_args.sysupgrade = False
    pacman_args.refresh = False

    # one status message
    aurman_status("initializing {}...".format(Colors.BOLD("aurman")), True)

    # analyzing installed packages
    try:
        installed_system = System(System.get_installed_packages())
    except InvalidInput:
        sys.exit(1)

    if installed_system.not_repo_not_aur_packages_list:
        aurman_status("the following packages are neither in known repos nor in the aur")
        for package in installed_system.not_repo_not_aur_packages_list:
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
            aurman_error("Packages you want to be not removed must be aur or repo packages.\n"
                         "   {} is not known.".format(Colors.BOLD(Colors.LIGHT_MAGENTA(name))))
            sys.exit(1)

    # for dep solving not to be removed has to be treated as wanted to install
    sanitized_names |= sanitized_not_to_be_removed

    # fetching ignored packages
    ignored_packages_names = Package.get_ignored_packages_names(pacman_args.ignore, pacman_args.ignoregroup,
                                                                upstream_system)
    # explicitly typed in names will not be ignored
    ignored_packages_names -= sanitized_names
    for ignored_packages_name in ignored_packages_names:
        if ignored_packages_name in upstream_system.all_packages_dict:
            if ignored_packages_name in installed_system.all_packages_dict:
                aurman_note("{} {} package {}".format(Colors.BOLD(Colors.LIGHT_MAGENTA("Ignoring")),
                                                      Colors.BOLD(Colors.LIGHT_CYAN("installed")),
                                                      Colors.BOLD(Colors.LIGHT_MAGENTA(ignored_packages_name))))

                upstream_system.all_packages_dict[ignored_packages_name] = installed_system.all_packages_dict[
                    ignored_packages_name]
            else:
                aurman_note("{} {} package {}".format(Colors.BOLD(Colors.LIGHT_MAGENTA("Ignoring")),
                                                      Colors.BOLD(Colors.LIGHT_BLUE("upstream ")),
                                                      Colors.BOLD(Colors.LIGHT_MAGENTA(ignored_packages_name))))

                del upstream_system.all_packages_dict[ignored_packages_name]

    # recreating upstream system
    if ignored_packages_names:
        upstream_system = System(list(upstream_system.all_packages_dict.values()))

    # if user entered --devel and not --repo, fetch all needed pkgbuilds etc. for the devel packages
    if devel and not repo:
        aurman_status("looking for new pkgbuilds of devel packages and fetch them...")
        for package in upstream_system.devel_packages_list:
            package.fetch_pkgbuild()
        try:
            for package in upstream_system.devel_packages_list:
                package.show_pkgbuild(noedit, show_changes, pgp_fetch, keyserver)
        except InvalidInput:
            sys.exit(1)
        for package in upstream_system.devel_packages_list:
            package.get_devel_version()

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

    aurman_status("calculating solutions...")
    if only_unfulfilled_deps:
        solutions = Package.dep_solving(concrete_packages_to_install, installed_system, upstream_system)
    else:
        solutions = Package.dep_solving(concrete_packages_to_install, System(()), upstream_system)

    # validates the found solutions and lets the user choose one of them, if there are more than one valid solutions
    try:
        chosen_solution = installed_system.validate_and_choose_solution(solutions, concrete_packages_to_install)
    except InvalidInput:
        aurman_error("we could not find a solution")
        aurman_error("if you think that there should be one, rerun aurman with the --deep_search flag")
        sys.exit(1)

    # needed because deep_search ignores installed packages
    if not only_unfulfilled_deps:
        pacman_args.needed = True

    # solution contains no packages
    if not chosen_solution:
        aurman_note("nothing to do... everything is up to date")
        sys.exit(0)

    try:
        installed_system.show_solution_differences_to_user(chosen_solution, upstream_system, noconfirm,
                                                           not only_unfulfilled_deps, solution_way)
    except InvalidInput:
        sys.exit(1)

    if not repo:
        aurman_status("looking for new pkgbuilds and fetch them...")
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
                package.show_pkgbuild(noedit, show_changes, pgp_fetch, keyserver)
        except InvalidInput:
            sys.exit(1)

    # install packages
    if not sudo_acquired:
        acquire_sudo()

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
                if package.name in sanitized_names and package.name not in sanitized_not_to_be_removed \
                        or ((package.name in installed_system.all_packages_dict)
                            and (installed_system.all_packages_dict[package.name].install_reason == 'explicit')):
                    as_explicit_container.add(package.name)

            pacman_args_copy = deepcopy(pacman_args)
            pacman_args_copy.targets = [package.name for package in package_chunk if
                                        package.name not in repo_packages_dict]

            pacman_args_copy.targets.extend(["{}/".format(repo_packages_dict[package.name]) + package.name
                                             for package in package_chunk if package.name in repo_packages_dict])
            pacman_args_copy.asdeps = True
            pacman_args_copy.asexplicit = False
            try:
                pacman(str(pacman_args_copy), False)
            except InvalidInput:
                sys.exit(1)

            if as_explicit_container:
                pacman("-D --asexplicit {}".format(" ".join(as_explicit_container)), True, sudo=True)
        # aur chunks always consist of one package
        else:
            package = package_chunk[0]
            package.build()
            try:
                if package.name in sanitized_names and package.name not in sanitized_not_to_be_removed \
                        or ((package.name in installed_system.all_packages_dict)
                            and (installed_system.all_packages_dict[package.name].install_reason == 'explicit')):
                    package.install(args_for_explicit)
                else:
                    package.install(args_for_dependency)
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
