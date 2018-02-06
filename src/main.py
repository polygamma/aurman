from parse_args import group_args
from sys import argv, exit
from utilities import *
from package_classes import *
from package_utilites import classify_packages, get_installed_aur_packages, what_to_install_with_deps, \
    check_versioning_and_conflicts, split_packages, order_aur_packages

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(funcName)s - %(levelname)s - %(message)s')


def process(args):
    operation = ""
    grouped_args = {}
    packages_of_user = []
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
        packages_of_user = grouped_args['aurman']['packages']
        del grouped_args['aurman']['packages']

    # if not -S or --sync, just redirect to pacman
    if operation not in ['S', 'sync']:
        args_as_string = args_to_string(grouped_args['other'])
        call_pacman(operation, args_as_string)
        return

    # -S or --sync
    # we got "packages_of_user" already
    sysupgrade = ('u' in grouped_args['aurman']) or ('sysupgrade' in grouped_args['aurman'])
    needed = 'needed' in grouped_args['aurman']
    noedit = 'noedit' in grouped_args['aurman']
    devel = 'devel' in grouped_args['aurman']

    if sysupgrade:
        if not sudo_acquired:
            acquire_sudo()
            sudo_acquired = True
        args_as_string = args_to_string(grouped_args['S'])
        call_pacman(operation, args_as_string)

    # dict containing the names as keys and concrete package instances as values
    # will also contain information of all already installed packages
    # will all in all contain all possibly needed information for packages
    classified_packages = classify_packages(packages_of_user)

    # delete -u --sysupgrade -y --refresh from -S dict
    # not needed anymore
    # note: we do not allow -y without -u
    s_dict = grouped_args['S']
    if 'u' in s_dict:
        del s_dict['u']
    if 'sysupgrade' in s_dict:
        del s_dict['sysupgrade']
    if 'y' in s_dict:
        del s_dict['y']
    if 'refresh' in s_dict:
        del s_dict['refresh']

    # packages_of_user contains now the concrete instances of the packages
    packages_of_user = [classified_packages[package_name] for package_name in packages_of_user]

    # this list will contain all packages which will be installed
    packages_going_to_install = []

    # if sysupgrade we need to check if all installed aur packages are installed in the latest version available
    if sysupgrade:
        installed_aur_packages = get_installed_aur_packages(classified_packages)

        # if devel fetch devel packages sources
        if devel:
            for package in installed_aur_packages:
                if isinstance(package, DevelPackage):
                    package.fetch_latest_sources(noedit)

        # not latest version installed, so update these packages
        for package in installed_aur_packages:
            if not package.installed_in_latest_version():
                packages_going_to_install.append(package)

    # not needed means reinstall no matter what
    if not needed:
        packages_going_to_install.extend(packages_of_user)

    # needed means just reinstall if not installed in latest version
    else:
        # if devel fetch devel packages sources
        if devel:
            for package in packages_of_user:
                if isinstance(package, DevelPackage):
                    package.fetch_latest_sources(noedit)

        for package in packages_of_user:
            if not package.installed_in_latest_version():
                packages_going_to_install.append(package)

    # we need to get all unfulfilled deps, too
    packages_going_to_install = what_to_install_with_deps(packages_going_to_install, classified_packages)
    # check for versioning and conflicts
    # exception will be thrown in case of unfulfilled deps, just logging info for conflicts (hf pacman)
    try:
        check_versioning_and_conflicts(packages_going_to_install, classified_packages)
    except InvalidInput:
        logging.error("Dep problem, exiting.")
        exit(1)

    aur_packages_to_install, repo_packages_to_install = split_packages(packages_going_to_install)
    # topologically sort the aur packages
    aur_packages_to_install = order_aur_packages(aur_packages_to_install)
    # if user does not want to install those packages
    if aur_packages_to_install or repo_packages_to_install:
        if not ask_user_install_packages(aur_packages_to_install, repo_packages_to_install):
            exit(1)

    # repo packages the user explicitly wanted
    repo_packages_explicitly_wanted = [package for package in repo_packages_to_install if package in packages_of_user]

    # append the packages to the pacman query
    args_to_parse = deepcopy(grouped_args['S'])
    args_to_parse[''] = [package.name for package in repo_packages_explicitly_wanted]
    args_as_string = args_to_string(args_to_parse)
    # install the repo packages
    if repo_packages_explicitly_wanted:
        if not sudo_acquired:
            acquire_sudo()
            sudo_acquired = True
        call_pacman(operation, args_as_string)

    # fetch all pkgbuilds of the aur packages
    for package in aur_packages_to_install:
        package.fetch_latest_pkgbuild_install_files()
    # show changed files to user
    if not noedit:
        for package in aur_packages_to_install:
            package.show_pkgbuild_install_files_to_user()

    if aur_packages_to_install:
        if not sudo_acquired:
            acquire_sudo()

    # aur packages the user explicitly wanted
    aur_packages_explicitly_wanted = [package for package in aur_packages_to_install if package in packages_of_user]

    # build packages
    for package in aur_packages_to_install:
        package.build()
        if package in aur_packages_explicitly_wanted:
            package.install(grouped_args['U'])
        else:
            args_with_asdeps = deepcopy(grouped_args['U'])
            args_with_asdeps['asdeps'] = []
            package.install(args_with_asdeps)


if __name__ == '__main__':
    try:
        process(argv[1:])
    except:
        logging.error("Unknown exception occurred.", exc_info=True)
