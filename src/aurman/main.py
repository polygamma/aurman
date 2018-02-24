import logging
from copy import deepcopy
from sys import argv

from aurman.classes import System, Package, PossibleTypes
from aurman.own_exceptions import InvalidInput
from aurman.parse_args import group_args, args_to_string
from aurman.print_help import help_to_print
from aurman.utilities import acquire_sudo, version_comparison
from aurman.wrappers import pacman

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(funcName)s - %(levelname)s - %(message)s')


def process(args):
    packages_of_user_names = []
    sudo_acquired = False

    # parse parameters of user
    try:
        operation, grouped_args = group_args(args)
    except InvalidInput:
        print(help_to_print)
        return

    # delete own pk parameter. Was just for parsing.
    if 'pk' in grouped_args['other']:
        grouped_args['other'][''] = grouped_args['other']['pk']
        del grouped_args['other']['pk']

    elif 'pk' in grouped_args['aurman']:
        packages_of_user_names = grouped_args['aurman']['pk']
        del grouped_args['aurman']['pk']

    # if not -S or --sync, just redirect to pacman
    if operation not in ['S', 'sync']:
        relevant_args = grouped_args['other']
        relevant_args[operation] = []
        args_as_string = args_to_string(relevant_args)
        try:
            pacman(args_as_string, False)
        except InvalidInput:
            return
        finally:
            return

    # -S or --sync
    # we got "packages_of_user_names" already
    sysupgrade = ('u' in grouped_args['aurman']) or ('sysupgrade' in grouped_args['aurman'])
    needed = 'needed' in grouped_args['aurman']
    noedit = 'noedit' in grouped_args['aurman']
    devel = 'devel' in grouped_args['aurman']
    only_unfulfilled_deps = 'deep_search' not in grouped_args['aurman']
    pgp_fetch = 'pgp_fetch' in grouped_args['aurman']
    noconfirm = 'noconfirm' in grouped_args['S']

    # do not allow -y without -u
    if ('y' in grouped_args['S'] or 'refresh' in grouped_args['S']) and not sysupgrade:
        logging.info("-y without -u is not allowed!")
        return

    # unrecognized parameters
    if grouped_args['other']:
        logging.info("The following parameters are not recognized yet: {}".format(grouped_args['other']))
        print(help_to_print)
        return

    # categorize user input
    for_us, for_pacman = Package.user_input_to_categories(packages_of_user_names)

    # in case of sysupgrade or packages relevant for pacman, call pacman
    if sysupgrade or for_pacman:
        if not sudo_acquired:
            acquire_sudo()
            sudo_acquired = True
        relevant_args = deepcopy(grouped_args['S'])
        relevant_args[''] = for_pacman
        relevant_args[operation] = []
        args_as_string = args_to_string(relevant_args)
        try:
            pacman(args_as_string, False)
        except InvalidInput:
            return

    if not sysupgrade and not for_us:
        return

    # delete -u --sysupgrade -y --refresh from -S dict
    # not needed anymore
    s_dict = grouped_args['S']
    if 'u' in s_dict:
        del s_dict['u']
    if 'sysupgrade' in s_dict:
        del s_dict['sysupgrade']
    if 'y' in s_dict:
        del s_dict['y']
    if 'refresh' in s_dict:
        del s_dict['refresh']

    print("\nanalyzing installed packages...")
    installed_system = System(System.get_installed_packages())

    print("fetching upstream repo packages...")
    upstream_system = System(System.get_repo_packages())

    print("fetching needed aur packages...")
    upstream_system.append_packages_by_name(for_us)
    # fetch info for all installed aur packages, too
    names_of_installed_aur_packages = [package.name for package in installed_system.aur_packages_list]
    names_of_installed_aur_packages.extend([package.name for package in installed_system.devel_packages_list])
    upstream_system.append_packages_by_name(names_of_installed_aur_packages)

    # if user entered --devel, fetch all needed pkgbuilds etc. for the devel packages
    if devel:
        print("looking for new pkgbuilds of devel packages and fetch them...")
        for package in upstream_system.devel_packages_list:
            package.fetch_pkgbuild()
        try:
            for package in upstream_system.devel_packages_list:
                package.show_pkgbuild(noedit)
                package.search_and_fetch_pgp_keys(pgp_fetch)
        except InvalidInput:
            return
        for package in upstream_system.devel_packages_list:
            package.get_devel_version()

    # checking which packages need to be installed
    if not needed:
        concrete_packages_to_install = [upstream_system.all_packages_dict[name] for name in for_us]
    else:
        possible_packages = [upstream_system.all_packages_dict[name] for name in for_us]
        concrete_packages_to_install = []
        for package in possible_packages:
            if package.name in installed_system.all_packages_dict:
                installed_package = installed_system.all_packages_dict[package.name]
                if version_comparison(installed_package.version, "<", package.version):
                    concrete_packages_to_install.append(package)
            else:
                concrete_packages_to_install.append(package)

    # in case of sysupgrade fetch all installed aur packages, of which newer versions are available
    if sysupgrade:
        installed_aur_packages = [package for package in installed_system.aur_packages_list]
        installed_aur_packages.extend([package for package in installed_system.devel_packages_list])
        for package in installed_aur_packages:
            upstream_package = upstream_system.all_packages_dict[package.name]
            if version_comparison(upstream_package.version, ">", package.version):
                if upstream_package not in concrete_packages_to_install:
                    concrete_packages_to_install.append(upstream_package)

    print("calculating solutions...")
    solutions = Package.dep_solving(concrete_packages_to_install, installed_system, upstream_system,
                                    only_unfulfilled_deps)

    # validates the found solutions and lets the user choose one of them, if there are more than one valid solutions
    try:
        chosen_solution = installed_system.validate_and_choose_solution(solutions, concrete_packages_to_install)
    except InvalidInput:
        print(
            "we could not find a solution.\nif you think that there should be one, rerun aurman with the --deep_search flag")
        return

    # needed because deep_search ignores installed packages
    if not only_unfulfilled_deps:
        for package in chosen_solution[:]:
            if (package.name not in for_us) and (package.name in installed_system.all_packages_dict) and (
                    version_comparison(installed_system.all_packages_dict[package.name].version, ">=",
                                       package.version)):
                chosen_solution.remove(package)

    # solution contains no packages
    if not chosen_solution:
        print("nothing to do... everything is up to date")
        return

    try:
        installed_system.show_solution_differences_to_user(chosen_solution, noconfirm)
    except InvalidInput:
        return

    # split packages
    repo_packages_names = []
    # for aur packages only sets of names needed
    explicit_aur_packages_names = set()
    for package in chosen_solution[:]:
        if package.type_of is PossibleTypes.REPO_PACKAGE:
            repo_packages_names.append(package.name)
            # concrete repo packages instances not needed anymore
            chosen_solution.remove(package)
        elif package.name in for_us or ((package.name in installed_system.all_packages_dict) and (
                installed_system.all_packages_dict[package.name].install_reason == 'explicit')):
            explicit_aur_packages_names.add(package.name)

    # install repo packages
    if not sudo_acquired:
        acquire_sudo()

    if repo_packages_names:
        relevant_args = deepcopy(grouped_args['S'])
        relevant_args[''] = repo_packages_names
        relevant_args[operation] = []
        relevant_args['asdeps'] = []
        args_as_string = args_to_string(relevant_args)
        try:
            pacman(args_as_string, False)
        except InvalidInput:
            return

    # generate pacman args for the aur packages
    relevant_args = deepcopy(grouped_args['U'])
    relevant_args['U'] = []

    args_for_explicit = args_to_string(relevant_args)
    relevant_args['asdeps'] = []
    args_for_dependency = args_to_string(relevant_args)

    # build and install aur packages
    print("looking for new pkgbuilds and fetch them...")
    for package in chosen_solution:
        if package.type_of is PossibleTypes.DEVEL_PACKAGE:
            continue
        package.fetch_pkgbuild()
    try:
        for package in chosen_solution:
            if package.type_of is PossibleTypes.DEVEL_PACKAGE:
                continue
            package.show_pkgbuild(noedit)
            package.search_and_fetch_pgp_keys(pgp_fetch)
    except InvalidInput:
        return

    for package in chosen_solution:
        package.build()
        try:
            if package.name in explicit_aur_packages_names:
                package.install(args_for_explicit)
            else:
                package.install(args_for_dependency)
        except InvalidInput:
            return


def main():
    try:
        process(argv[1:])
    except (SystemExit, KeyboardInterrupt):
        pass
    except:
        logging.error("", exc_info=True)


if __name__ == '__main__':
    main()
