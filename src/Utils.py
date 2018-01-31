import requests
import json
import Exceptions
import logging
import subprocess
import threading
import time
import Package

# endings of development packages
develendings = ["bzr", "git", "hg", "svn", "daily", "nightly"]

# AurJson variables
query_url = "https://aur.archlinux.org/rpc/?v=5&type=info"
query_prefix = "&arg[]="


def install_packages(package_names):
    """
    Installs/Updates the packages with the names defined in package_names
    and also all installed packages

    Exceptions: Exceptions.ConnectionProblem,
                Exceptions.InvalidInput

    :param package_names: The names of the packages to install/update
    """

    # get sudo and fetch latest databases
    acquire_sudo()
    fetch_current_databases()

    # remove duplicate names
    package_names = list(set(package_names))

    # fetch all installed non repo packages
    installed_packages_names = all_installed_not_repo_packages()

    # those packages are 100% not repo packages
    all_dict, ordered_dict = Package.Package.retrieve_all_packages_information(installed_packages_names, True)
    for package in ordered_dict["devel"]:
        package.fetch_current_sources()

    relevant_packages = ordered_dict["aur"]
    relevant_packages.extend(ordered_dict["devel"])

    # find packages which are not up to date
    for package in relevant_packages:
        if not package.is_installed_and_latest():
            package_names.append(package.name)

    # now check the packages of the user + outdated installed packages
    all_dict, ordered_dict = Package.Package.retrieve_all_packages_information(package_names)
    for package in ordered_dict["devel"]:
        package.fetch_current_sources()

    # which packages need to be installed all in all
    packages_to_install = what_to_install(package_names, all_dict, ordered_dict)

    # in which order do they have to be installed
    ordered_aur_packages = check_conflicts_and_order(all_dict, packages_to_install[0], packages_to_install[1])

    # fetch needed pkgbuilds and show them to the user if needed
    for aur_package in ordered_aur_packages:
        # if new pkgbuild
        if aur_package.fetch_pkgbuild():
            if not aur_package.show_pkgbuild_to_user():
                logging.info("PKGBUILD not okay!")
                raise Exceptions.InvalidInput("PKGBUILD not okay!")

    explicit_repo_packages = []
    implicit_repo_packages = []

    # find repo packages that are only needed as deps
    for repo_package_name in packages_to_install[0]:
        if repo_package_name in package_names:
            explicit_repo_packages.append(repo_package_name)
        else:
            implicit_repo_packages.append(repo_package_name)

    # install repo packages with --sysupgrade
    Package.Package.install_repo_packages(explicit_repo_packages, implicit_repo_packages, "--sysupgrade")

    # find aur packages that are only needed as deps
    for aur_package in ordered_aur_packages:
        if aur_package.name in package_names:
            aur_package.install_package()
        else:
            aur_package.install_package("--asdeps")


def all_installed_not_repo_packages():
    """
    Returns all installed packages which are not from the repos

    Exception: Exceptions.InvalidInput

    :return:    a list containing the names of all installed not repo packages
    """
    pacman_return = subprocess.run("pacman -Qm", shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   universal_newlines=True)
    if pacman_return.returncode != 0:
        logging.info("could not fetch the list of installed aur packages")
        raise Exceptions.InvalidInput("could not fetch the list of installed aur packages")

    pacman_lines = pacman_return.stdout.strip().splitlines()

    return [line.split()[0] for line in pacman_lines]


def check_conflicts_and_order(packages_dict, repo_package_names, aur_package_names):
    """
    Checks for conflicts and orders the aur packages so that
    they may be installed.

    Exception: Exceptions.InvalidInput


    :param packages_dict:           The first dict from the tuple of Package.retrieve_all_packages_information return value,
                                    which holds information for all packages which are be potentially needed
                                    to be installed

    :param repo_package_names:      list of names of the repo packages to get installed
    :param aur_package_names:       list of names of the aur packages to get installed
    :return:                        the order in which the aur packages should be installed
                                    (concrete package objects in list)
    """

    aur_order = []

    # sort the input
    aur_package_names = list(aur_package_names)
    repo_packages = [packages_dict[name] for name in repo_package_names]
    aur_packages = [packages_dict[name] for name in aur_package_names]
    all_packages = repo_packages
    all_packages.extend(aur_packages)

    # look for conflicts
    conflict_return = Package.Package.is_any_conflict(all_packages)
    if conflict_return[0]:
        logging.info("Conflict between %s and %s", conflict_return[1], conflict_return[2])
        raise Exceptions.InvalidInput("conflict detected")

    # while there are packages which need to get installed
    while aur_packages:
        for current_package in aur_packages[:]:
            # all dependencies fulfilled
            if current_package.ready_to_install(aur_package_names):
                aur_packages.remove(current_package)
                aur_package_names.remove(current_package.name)
                aur_order.append(current_package)
                break
        else:
            logging.info("cycle in deps")
            raise Exceptions.InvalidInput("cycle in deps")

    return aur_order


def meets_version_requirement(version_available, version_comparator,
                              version_needed):
    """
    Format: (1.3.37,            >=,                 1.0.1)
            (version_available, version_comparator, version_needed)

    :param version_available:   The version available
    :param version_comparator:  The comparator
    :param version_needed:      The needed version
    :return:    True if the requirement is fulfilled, False otherwise
    """

    version_cmp = compare_versions(version_available, version_needed)

    if version_cmp < 0:
        return version_comparator == "<" or version_comparator == "<="
    elif version_cmp == 0:
        return not (version_comparator == "<" or version_comparator == ">")
    else:
        return version_comparator == ">" or version_comparator == ">="


def what_to_install(packages, packages_dict, packages_ordered_dict):
    """
    Decides what needs to be installed all in all so that
    the packages with the names defined in "packages" get installed in the latest
    versions available.

    Exception: Exceptions.InvalidInput


    :param packages:        The names of the packages to install
    :param packages_dict:   The first dict from the tuple of Package.retrieve_all_packages_information return value,
                            which holds information for all packages which are be potentially needed
                            to be installed

    :param packages_ordered_dict:  The second dict from the tuple of Package.retrieve_all_packages_information
                            return value, which holds information for all packages which are be potentially needed
                            to be installed

    :return:                Tuple containing two items.

                            First: A set containing all repo packages and groups (names of the packages)
                            Second: A set containing all aur/devel packages    (names of the packages)
    """

    # sort input
    package_tuples_to_check = [split_name_with_versioning(package) for package in packages]
    repo_or_group_packages = []
    aur_or_devel_packages = []

    # while there are packages which need to be checked
    while package_tuples_to_check:
        new_package_tuples_to_check = []

        for current_package_tuple in package_tuples_to_check:
            current_package_name = current_package_tuple[0]

            if current_package_name not in packages_dict:
                logging.info("package %s not found", current_package_name)
                raise Exceptions.InvalidInput("package not found")

            # pacman needs to handle this
            if current_package_name in [package.name for package in packages_ordered_dict["not_valid"]]:
                logging.debug("package %s not valid", current_package_name)
                repo_or_group_packages.append(current_package_tuple)
                continue
                # raise Exceptions.InvalidInput("package not valid")

            current_package = packages_dict[current_package_name]

            # fine, nothing to do here
            if current_package.is_installed_and_latest():
                continue

            current_package_comparator = current_package_tuple[1]
            current_package_version_needed = current_package_tuple[2]
            # dirty hack to find out, if we need to do a version check
            needs_specific_package_version = bool(current_package_comparator)

            # if no version requirement or requirement fulfilled
            if not needs_specific_package_version or meets_version_requirement(
                    current_package.newest_version_available(), current_package_comparator,
                    current_package_version_needed):

                if current_package.in_repo_or_group:
                    repo_or_group_packages.append(current_package_tuple)
                else:
                    assert current_package.in_aur or current_package.is_devel
                    # for aur and devel packages we need to check the dependencies if we havent checked them
                    for dependency in current_package.dependencies:
                        dep_tuple = split_name_with_versioning(dependency)
                        if (dep_tuple not in repo_or_group_packages) and (dep_tuple not in aur_or_devel_packages) and (
                                dep_tuple not in new_package_tuples_to_check):
                            new_package_tuples_to_check.append(dep_tuple)

                    aur_or_devel_packages.append(current_package_tuple)

            else:
                logging.info("version requirement of %s not fulfilled", str(current_package_tuple))
                raise Exceptions.InvalidInput("version requirement not fulfilled")

        package_tuples_to_check = new_package_tuples_to_check

    # now we only need the names
    return set([curr_tuple[0] for curr_tuple in repo_or_group_packages]), set(
        [curr_tuple[0] for curr_tuple in aur_or_devel_packages])


def ask_user(question, default):
    """
    Asks the user a yes/no question.

    :param question:    The question to ask
    :param default:     The default answer, if user presses enter.
                        True for yes, False for no
    :return:    yes: True, no: False
    """

    yes = ["y"]
    no = ["n"]
    if default:
        yes.append("")
        choices = " Y/n: "
    else:
        no.append("")
        choices = " N/y: "

    user_choice = "I am not really sure right now"
    while (user_choice not in yes) and (user_choice not in no):
        user_choice = str(input(question + choices)).strip().lower()

    return user_choice in yes


def split_name_with_versioning(name):
    """
    Splits name with versioning into its parts.
    e.g. "gunnar>=1.3.3.7" -> ("gunnar", ">=", "1.3.3.7")

    :param name:    the name to split
    :return:    the parts of the name in a tuple
                (name, comparison-operator, version)
    """

    comparison_operators = (">", "<", "=")
    start_operator = len(name)
    end_operator = -1

    for comparison_operator in comparison_operators:
        if comparison_operator in name:
            index = name.index(comparison_operator)
            if index < start_operator:
                start_operator = index
            if index > end_operator:
                end_operator = index

    return name[:start_operator], name[start_operator:end_operator + 1], name[max(end_operator + 1, start_operator):]


def compare_versions(version1, version2):
    """
    vercmp wrapper.
    https://www.archlinux.org/pacman/vercmp.8.html


    :param version1:    ver1
    :param version2:    ver2
    :return:    < 0 : if ver1 < ver2
                = 0 : if ver1 == ver2
                > 0 : if ver1 > ver2
    """
    return int(subprocess.run("vercmp '" + version1 + "' '" + version2 + "'", shell=True, stdout=subprocess.PIPE,
                              universal_newlines=True).stdout)


def strip_versioning(name):
    """
    Removes versioning from a package name.
    e.g. foo>=3.1 -> foo


    :param name: the name to strip the versioning from
    :return: the name without versioning
    """
    return split_name_with_versioning(name)[0]


def fetch_current_databases():
    """
    Fetches the current package databases

    Exception: Exceptions.ConnectionProblem
    """
    if subprocess.run("sudo pacman -Sy", shell=True).returncode != 0:
        logging.info("Pacman was not able to update the databases")
        raise Exceptions.ConnectionProblem("Pacman was not able to update the databases")

    logging.debug("Fetched databases successfully")


def acquire_sudo():
    """
    sudo loop since we want sudo forever
    """

    def sudo_loop():
        while True:
            subprocess.run("sudo -v", shell=True, stdout=subprocess.DEVNULL)
            logging.debug("sudo acquired")
            time.sleep(120)

    subprocess.run("sudo -v", shell=True)
    logging.debug("sudo acquired")
    t = threading.Thread(target=sudo_loop)
    t.daemon = True
    t.start()


def is_devel(name):
    """
    Checks if a given package is a development package

    :param name:    the name of the package
    :return:    True if it is a development package, False otherwise
    """
    global develendings

    for develending in develendings:
        if name.endswith("-" + develending):
            return True

    return False


def get_aur_info(package_names):
    """
    Fetches information of AUR packages via the AurJson interface
    https://wiki.archlinux.org/index.php/AurJson

    Exceptions: Exceptions.ConnectionProblem,
                Exceptions.InvalidInput

    :param package_names:   A list containing the names of the packages
    :return:    Dict containing the fetched information

                {
                    "package_name1":
                        {
                            "PackageBase": "PackageBase",
                            "Version": "Version",
                            "Depends": ["dep1", ...],
                            "MakeDepends": ["dep1", ...],
                            "Conflicts": ["pack1", ...]
                        },
                    "package_name2":
                        {
                            ...
                        },
                    ...
                }
    """
    global query_url, query_prefix

    return_dict = {}
    url_to_call = query_url
    for name in package_names:
        url_to_call += query_prefix + name

    try:
        json_dict = json.loads(requests.get(url_to_call, timeout=5).text)
    except requests.exceptions.RequestException:
        logging.info(str(package_names), exc_info=True)
        raise Exceptions.ConnectionProblem("Request to AUR failed.")
    except json.JSONDecodeError:
        logging.info(str(package_names), exc_info=True)
        raise Exceptions.InvalidInput("JSON of AUR malformed.")

    try:
        results = json_dict["results"]
        for package in results:
            name = package["Name"]
            return_dict[name] = {}
            return_dict[name]["PackageBase"] = package["PackageBase"]
            return_dict[name]["Version"] = package["Version"]
            return_dict[name]["Depends"] = package.get("Depends", [])
            return_dict[name]["MakeDepends"] = package.get("MakeDepends", [])
            return_dict[name]["Conflicts"] = package.get("Conflicts", [])

    except KeyError:
        logging.info(str(package_names), exc_info=True)
        raise Exceptions.InvalidInput("JSON of AUR malformed.")

    logging.debug("%s parsed without errors", str(package_names))
    return return_dict
