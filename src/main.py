from copy import deepcopy

from classes import System, Package
from sys import argv
import logging
from own_exceptions import InvalidInput
from parse_args import group_args, args_to_string
from wrappers import pacman
from utilities import acquire_sudo, version_comparison

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(funcName)s - %(levelname)s - %(message)s')


def process(args):
    operation = ""
    grouped_args = {}
    packages_of_user_names = []
    sudo_acquired = False

    try:
        operation, grouped_args = group_args(args)
    except InvalidInput:
        logging.error("Parsing the arguments %s failed, exiting.", str(args))
        exit(1)

    # delete own packages parameter. Was just for parsing.
    if 'packages' in grouped_args['other']:
        grouped_args['other'][''] = grouped_args['other']['packages']
        del grouped_args['other']['packages']

    elif 'packages' in grouped_args['aurman']:
        packages_of_user_names = grouped_args['aurman']['packages']
        del grouped_args['aurman']['packages']

    # if not -S or --sync, just redirect to pacman
    if operation not in ['S', 'sync']:
        relevant_args = grouped_args['other']
        relevant_args[operation] = []
        args_as_string = args_to_string(relevant_args)
        pacman(args_as_string, False)
        return

    # -S or --sync
    # we got "packages_of_user_names" already
    sysupgrade = ('u' in grouped_args['aurman']) or ('sysupgrade' in grouped_args['aurman'])
    needed = 'needed' in grouped_args['aurman']
    noedit = 'noedit' in grouped_args['aurman']
    devel = 'devel' in grouped_args['aurman']
    only_unfulfilled_deps = 'deep_search' not in grouped_args['aurman']

    # categorize user input
    for_us, for_pacman = Package.user_input_to_categories(packages_of_user_names)

    if sysupgrade or for_pacman:
        if not sudo_acquired:
            acquire_sudo()
            sudo_acquired = True
        relevant_args = deepcopy(grouped_args['S'])
        relevant_args[''] = for_pacman
        relevant_args[operation] = []
        args_as_string = args_to_string(relevant_args)
        pacman(args_as_string, False)

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

    print("installed system fetching...")
    installed_system = System(System.get_installed_packages())

    print("upstream system fetching...")
    upstream_system = System(System.get_repo_packages())

    print("own packages fetching...")
    upstream_system.append_packages_by_name(for_us)
    names_of_installed_aur_packages = [package.name for package in installed_system.aur_packages_list]
    names_of_installed_aur_packages.extend([package.name for package in installed_system.devel_packages_list])
    upstream_system.append_packages_by_name(names_of_installed_aur_packages)

    print("fetching pkgbuilds...")
    for package in upstream_system.aur_packages_list:
        break
        package.fetch_pkgbuild()
    for package in upstream_system.devel_packages_list:
        break
        package.fetch_pkgbuild()
    if not noedit:
        for package in upstream_system.aur_packages_list:
            break
            package.show_pkgbuild()
        for package in upstream_system.devel_packages_list:
            break
            package.show_pkgbuild()
    if devel:
        for package in upstream_system.devel_packages_list:
            break
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

    chosen_solution = installed_system.validate_and_choose_solution(solutions, concrete_packages_to_install)

    installed_system.show_solution_differences_to_user(chosen_solution)

    # installing comes later


if __name__ == '__main__':
    try:
        process(argv[1:])
    except:
        pass
