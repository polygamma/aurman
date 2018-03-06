import logging
from copy import deepcopy
from sys import argv, stdout

from pycman.config import PacmanConfig

from aurman.bash_completion import possible_completions
from aurman.classes import System, Package, PossibleTypes
from aurman.coloring import aurman_error, aurman_status, aurman_note, Colors
from aurman.help_printing import aurman_help
from aurman.own_exceptions import InvalidInput
from aurman.parse_args import PacmanOperations, parse_pacman_args
from aurman.utilities import acquire_sudo, version_comparison, search_and_print
from aurman.wrappers import pacman, expac

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(funcName)s - %(levelname)s - %(message)s')


def process(args):
    import aurman.aur_utilities

    sudo_acquired = False

    # parse parameters of user
    try:
        pacman_args = parse_pacman_args(args)
    except InvalidInput:
        aurman_note("aurman --help or aurman -h")
        return

    # show help
    if pacman_args.operation is PacmanOperations.HELP:
        # remove colors in case of not terminal
        if stdout.isatty():
            print(aurman_help)
        else:
            print(Colors.strip_colors(str(aurman_help)))
        return

    # show version
    if pacman_args.operation is PacmanOperations.VERSION:
        # remove colors in case of not terminal
        if stdout.isatty():
            aurman_note(expac("-Q", ("v",), ("aurman-git",))[0])
        else:
            print(expac("-Q", ("v",), ("aurman-git",))[0])
        return

    # if not -S or --sync, just redirect to pacman
    if pacman_args.operation is not PacmanOperations.SYNC:
        try:
            if pacman_args.operation in [PacmanOperations.UPGRADE, PacmanOperations.REMOVE, PacmanOperations.DATABASE]:
                pacman(" ".join(args), False, sudo=True)
            else:
                pacman(" ".join(args), False, sudo=False)
        except InvalidInput:
            return
        finally:
            return

    # -S or --sync
    packages_of_user_names = list(set(pacman_args.targets))  # targets of the aurman command without duplicates
    sysupgrade = pacman_args.sysupgrade  # if -u or --sysupgrade
    needed = pacman_args.needed  # if --needed
    noedit = pacman_args.noedit  # if --noedit
    devel = pacman_args.devel  # if --devel
    only_unfulfilled_deps = not pacman_args.deep_search  # if not --deep_search
    pgp_fetch = pacman_args.pgp_fetch  # if --pgp_fetch
    noconfirm = pacman_args.noconfirm  # if --noconfirm
    search = pacman_args.search  # list containing the specified strings for -s and --search
    solution_way = pacman_args.solution_way  # if --solution_way

    not_remove = pacman_args.holdpkg  # list containing the specified packages for --holdpkg
    # if --holdpkg_conf append holdpkg from pacman.conf
    if pacman_args.holdpkg_conf:
        not_remove.extend(PacmanConfig(conf="/etc/pacman.conf").options['HoldPkg'])
    # remove duplicates
    not_remove = list(set(not_remove))

    aur = pacman_args.aur  # do only aur things
    repo = pacman_args.repo  # do only repo things
    if repo and aur:
        aurman_error("--repo and --aur is not what you want")
        return

    if pacman_args.keyserver:
        keyserver = pacman_args.keyserver[0]
    else:
        keyserver = None

    if pacman_args.domain:
        aurman.aur_utilities.aur_domain = pacman_args.domain[0]

    # do not allow -y without -u
    if pacman_args.refresh and not sysupgrade:
        aurman_error("-y without -u is not allowed!")
        return

    # unrecognized parameters
    if pacman_args.invalid_args:
        aurman_error("The following parameters are not recognized yet: {}".format(pacman_args.invalid_args))
        aurman_note("aurman --help or aurman -h")
        return

    # if user just wants to search
    if search:
        if not repo:
            installed_system = System(System.get_installed_packages())
        else:
            installed_system = None
        search_and_print(search, installed_system, str(pacman_args), repo, aur)
        return

    # groups are for pacman
    groups = pacman("-Sg", True, sudo=False)
    groups_chosen = []
    for name in packages_of_user_names[:]:
        if name in groups:
            groups_chosen.append(name)
            packages_of_user_names.remove(name)

    # in case of sysupgrade or groups to install and not --aur, call pacman
    if (sysupgrade or groups_chosen) and not aur:
        if not sudo_acquired:
            acquire_sudo()
            sudo_acquired = True
        pacman_args_copy = deepcopy(pacman_args)
        pacman_args_copy.targets = groups_chosen
        try:
            pacman(str(pacman_args_copy), False)
        except InvalidInput:
            return

    # nothing to do for us
    if not sysupgrade and not packages_of_user_names:
        return

    # delete -u --sysupgrade -y --refresh from parsed args
    # not needed anymore
    pacman_args.sysupgrade = False
    pacman_args.refresh = False

    # one status message
    aurman_status("initializing {}...".format(Colors.BOLD("aurman")), True)

    # analyzing installed packages
    installed_system = System(System.get_installed_packages())

    if installed_system.not_repo_not_aur_packages_list:
        aurman_status("the following packages are neither in known repos nor in the aur")
        for package in installed_system.not_repo_not_aur_packages_list:
            aurman_note("{}".format(Colors.BOLD(Colors.LIGHT_MAGENTA(package))))

    # fetching upstream repo packages...
    if not aur:
        upstream_system = System(System.get_repo_packages())
    else:
        upstream_system = System(())

    # fetching needed aur packages
    if not repo:
        upstream_system.append_packages_by_name(packages_of_user_names)
        # fetch info for all installed aur packages, too
        names_of_installed_aur_packages = ["aur/" + package.name for package in installed_system.aur_packages_list]
        names_of_installed_aur_packages.extend(
            ["aur/" + package.name for package in installed_system.devel_packages_list])
        upstream_system.append_packages_by_name(names_of_installed_aur_packages)

    # sanitize user input
    try:
        sanitized_names = upstream_system.sanitize_user_input(packages_of_user_names)
        sanitized_not_to_be_removed = installed_system.sanitize_user_input(not_remove)
    except InvalidInput:
        return

    # names to not be removed must be also known on the upstream system,
    # otherwise aurman solving cannot handle this case.
    for name in sanitized_not_to_be_removed:
        if name not in upstream_system.all_packages_dict:
            aurman_error("Packages you want to be not removed must be aur or repo packages.\n"
                         "   {} is not known.".format(Colors.BOLD(Colors.LIGHT_MAGENTA(name))))
            return

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
                package.show_pkgbuild(noedit)
                package.search_and_fetch_pgp_keys(pgp_fetch, keyserver)
        except InvalidInput:
            return
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
                if version_comparison(installed_package.version, "<", package.version):
                    concrete_packages_to_install.append(package)
            else:
                concrete_packages_to_install.append(package)

    # in case of sysupgrade and not --repo fetch all installed aur packages, of which newer versions are available
    if sysupgrade and not repo:
        installed_aur_packages = [package for package in installed_system.aur_packages_list]
        installed_aur_packages.extend([package for package in installed_system.devel_packages_list])
        for package in installed_aur_packages:
            # must not be that we have not received the upstream information
            assert package.name in upstream_system.all_packages_dict
            upstream_package = upstream_system.all_packages_dict[package.name]
            if version_comparison(upstream_package.version, ">", package.version):
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
        return

    # needed because deep_search ignores installed packages
    if not only_unfulfilled_deps:
        pacman_args.needed = True

    # solution contains no packages
    if not chosen_solution:
        aurman_note("nothing to do... everything is up to date")
        return

    try:
        installed_system.show_solution_differences_to_user(chosen_solution, upstream_system, noconfirm,
                                                           not only_unfulfilled_deps, solution_way)
    except InvalidInput:
        return

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
                package.show_pkgbuild(noedit)
                package.search_and_fetch_pgp_keys(pgp_fetch, keyserver)
        except InvalidInput:
            return

    # install packages
    if not sudo_acquired:
        acquire_sudo()

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
            pacman_args_copy.targets = [package.name for package in package_chunk]
            pacman_args_copy.asdeps = True
            pacman_args_copy.asexplicit = False
            try:
                pacman(str(pacman_args_copy), False)
            except InvalidInput:
                return

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
                return


def main():
    try:
        # auto completion
        if argv[1] == "--auto_complete":
            possible_completions()
            return

        # normal call
        process(argv[1:])
    except (SystemExit, KeyboardInterrupt, PermissionError):
        pass
    except:
        logging.error("", exc_info=True)


if __name__ == '__main__':
    main()
