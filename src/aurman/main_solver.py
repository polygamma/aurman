import fnmatch
import json
import logging
import os
import sys
from typing import Sequence, Set, Dict, List

from pycman.config import PacmanConfig

from aurman.aur_utilities import AurVars
from aurman.classes import System, Package, PossibleTypes
from aurman.coloring import aurman_error, aurman_note, Colors
from aurman.help_printing import aurmansolver_help
from aurman.own_exceptions import InvalidInput
from aurman.parse_args import parse_pacman_args, PacmanOperations
from aurman.parsing_config import read_config, AurmanConfig
from aurman.utilities import version_comparison, strip_versioning_from_name
from aurman.wrappers import makepkg

# you may want to switch to logging.DEBUG
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(funcName)s - %(levelname)s - %(message)s')


def sanitize_user_input(user_input: Sequence[str], system: 'System') -> Set[str]:
    """
    Finds the names of the packages for the user_input
    Needed since user may also specify the version of a package,
    hence package1>1.0 may yield package1 since package1 has version 2.0

    :param user_input:      The user input in a sequence
    :param system:          The system to check the providing of
    :return:                A set containing the packages names
    """
    sanitized_names = set()
    for name in user_input:
        providers_for_name = system.provided_by(name)
        if not providers_for_name:
            aurman_error("No providers for {} found.".format(Colors.BOLD(Colors.LIGHT_MAGENTA(name))))
            sys.exit(1)
        elif len(providers_for_name) == 1:
            sanitized_names.add(providers_for_name[0].name)
        # more than one provider
        else:
            dep_name = strip_versioning_from_name(name)
            providers_names = [package.name for package in providers_for_name]
            if dep_name in providers_names:
                sanitized_names.add(dep_name)
            else:
                aurman_error(
                    "Multiple providers found for {}\n"
                    "None of the providers has the name of the dep without versioning.\n"
                    "The providers are: {}".format(
                        Colors.BOLD(Colors.LIGHT_MAGENTA(name)),
                        ", ".join([system.repo_of_package(provider_for_name) for provider_for_name in providers_names])
                    )
                )
                sys.exit(1)

    return sanitized_names


def parse_parameters(args: List[str]):
    """
    parses the parameters of the user
    :param args: the args to parse
    :return: the parsed args
    """
    try:
        return parse_pacman_args(args)
    except InvalidInput:
        aurman_note("aurmansolver --help or aurmansolver -h")
        sys.exit(1)


def show_help() -> None:
    """
    shows the help of aurmansolver
    """
    # remove colors in case of not terminal
    if sys.stdout.isatty():
        print(aurmansolver_help)
    else:
        print(Colors.strip_colors(str(aurmansolver_help)))
    sys.exit(0)


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


class SolutionEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, PossibleTypes):
            return obj.name
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, Package):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)


def process(args):
    try:
        read_config()  # read config - available via AurmanConfig.aurman_config
    except InvalidInput:
        sys.exit(1)

    if os.getuid() == 0:
        aurman_error("Do not run aurman with sudo")
        sys.exit(1)

    # parse parameters of user
    pacman_args = parse_parameters(args)

    if pacman_args.operation is PacmanOperations.HELP:
        show_help()

    if pacman_args.operation is not PacmanOperations.SYNC or pacman_args.invalid_args:
        sys.exit(1)

    # -S or --sync
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

    # nothing to do for us
    if not sysupgrade and not packages_of_user_names:
        sys.exit(1)

    needed = pacman_args.needed  # if --needed
    devel = pacman_args.devel  # if --devel
    only_unfulfilled_deps = not pacman_args.deep_search  # if not --deep_search

    not_remove = pacman_args.holdpkg  # list containing the specified packages for --holdpkg
    # if --holdpkg_conf append holdpkg from pacman.conf
    if pacman_args.holdpkg_conf:
        not_remove.extend(PacmanConfig(conf="/etc/pacman.conf").options['HoldPkg'])
    # remove duplicates
    not_remove = list(set(not_remove))

    aur = pacman_args.aur  # do only aur things
    repo = pacman_args.repo  # do only repo things
    rebuild = pacman_args.rebuild  # if --rebuild
    # if to pass -A to makepkg
    ignore_arch = 'miscellaneous' in AurmanConfig.aurman_config and \
                  'ignore_arch' in AurmanConfig.aurman_config['miscellaneous']

    if repo and aur:
        aurman_error("--repo and --aur is not what you want")
        sys.exit(1)

    if pacman_args.domain:
        AurVars.aur_domain = pacman_args.domain[0]

    # change aur rpc timeout if set by the user
    if 'miscellaneous' in AurmanConfig.aurman_config \
            and 'aur_timeout' in AurmanConfig.aurman_config['miscellaneous']:
        AurVars.aur_timeout = int(AurmanConfig.aurman_config['miscellaneous']['aur_timeout'])

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
        if not pacman_args.show_unknown:
            logging.debug("the following packages are neither in known repos nor in the aur")
            for package in packages_to_show:
                logging.debug("{}".format(Colors.BOLD(Colors.LIGHT_MAGENTA(package))))
        else:
            print("\n".join([package.name for package in packages_to_show]))

    if pacman_args.show_unknown:
        sys.exit(0)

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
    sanitized_names = sanitize_user_input(packages_of_user_names, upstream_system)
    sanitized_not_to_be_removed = sanitize_user_input(not_remove, installed_system)

    # names to not be removed must be also known on the upstream system,
    # otherwise aurman solving cannot handle this case.
    for name in sanitized_not_to_be_removed:
        if name not in upstream_system.all_packages_dict:
            aurman_error(
                "Packages you want to be not removed must be aur or repo packages.\n"
                "   {} is not known.".format(
                    Colors.BOLD(Colors.LIGHT_MAGENTA(name))
                )
            )
            sys.exit(1)

    # for dep solving not to be removed has to be treated as wanted to install
    sanitized_names |= sanitized_not_to_be_removed

    # fetching ignored packages
    ignored_packages_names = Package.get_ignored_packages_names(
        pacman_args.ignore, pacman_args.ignoregroup, upstream_system, installed_system, True
    )
    # explicitly typed in names will not be ignored
    ignored_packages_names -= sanitized_names
    for ignored_packages_name in ignored_packages_names:
        if ignored_packages_name in upstream_system.all_packages_dict:
            if ignored_packages_name in installed_system.all_packages_dict:
                logging.debug("{} {} package {}".format(Colors.BOLD(Colors.LIGHT_MAGENTA("Ignoring")),
                                                        Colors.BOLD(Colors.LIGHT_CYAN("installed")),
                                                        Colors.BOLD(Colors.LIGHT_MAGENTA(ignored_packages_name))))

                upstream_system.all_packages_dict[ignored_packages_name] = installed_system.all_packages_dict[
                    ignored_packages_name]
            else:
                logging.debug("{} {} package {}".format(Colors.BOLD(Colors.LIGHT_MAGENTA("Ignoring")),
                                                        Colors.BOLD(Colors.LIGHT_BLUE("upstream ")),
                                                        Colors.BOLD(Colors.LIGHT_MAGENTA(ignored_packages_name))))

                del upstream_system.all_packages_dict[ignored_packages_name]
        elif ignored_packages_name in installed_system.all_packages_dict:
            logging.debug("{} {} package {}".format(Colors.BOLD(Colors.LIGHT_MAGENTA("Ignoring")),
                                                    Colors.BOLD(Colors.LIGHT_CYAN("installed")),
                                                    Colors.BOLD(Colors.LIGHT_MAGENTA(ignored_packages_name))))

    # recreating upstream system
    if ignored_packages_names:
        upstream_system = System(list(upstream_system.all_packages_dict.values()))

    # if user entered --devel and not --repo, fetch all current versions of devel packages
    if devel and not repo:
        for package in upstream_system.devel_packages_list:
            package_dir = os.path.join(Package.cache_dir, package.pkgbase)
            if not os.path.isdir(package_dir):
                aurman_error("Package dir of {} not found".format(Colors.BOLD(Colors.LIGHT_MAGENTA(package.name))))
                sys.exit(1)
            if not ignore_arch:
                makepkg(["-odc"], True, package_dir)
            else:
                makepkg(["-odcA"], True, package_dir)

            package.version = package.version_from_srcinfo()

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

    # calc solutions
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

    # fetch valid solutions
    sol_tuples = installed_system.validate_solutions(solutions, concrete_packages_to_install)
    valid_solutions = [sol_tuple[1] for sol_tuple in sol_tuples]
    if not valid_solutions:
        aurman_error("we could not find a solution")
        aurman_error("if you think that there should be one, rerun aurman with the --deep_search flag")
        sys.exit(1)

    print(
        json.dumps(
            [valid_solutions, installed_system.differences_between_systems([sol_tuple[0] for sol_tuple in sol_tuples])],
            cls=SolutionEncoder, indent=4
        )
    )


def main():
    try:
        process(sys.argv[1:])
    except SystemExit as e:
        sys.exit(e)
    except:
        logging.error("", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
