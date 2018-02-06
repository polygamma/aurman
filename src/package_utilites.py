from subprocess import run, PIPE, DEVNULL
import logging
from own_exceptions import *
import utilities
import package_classes
import aur_utilities
import copy


def call_pacman(operation, args_as_string, dir_to_execute=None):
    if len(operation) == 1:
        pacman_query = "sudo pacman -" + operation + " " + args_as_string
    else:
        pacman_query = "sudo pacman --" + operation + " " + args_as_string

    if dir_to_execute is None:
        if run(pacman_query, shell=True).returncode != 0:
            logging.error("Pacman query %s failed", pacman_query)
            raise InvalidInput()
    else:
        if run(pacman_query, shell=True, cwd=dir_to_execute).returncode != 0:
            logging.error("Pacman query %s failed", pacman_query)
            raise InvalidInput()


def classify_packages(package_names):
    """
    Classifies package_names.
    Does this until all needed not fulfilled dependencies are also classified.
    :param package_names:   The names of the packages to classify in a list
    :return:                Dict containing the classified packages.
                            {
                                "name1": package1,
                                "name2": package2,
                                ...
                            }
    """

    installed_packages_lines = run("pacman -Q", shell=True, universal_newlines=True, stdout=PIPE,
                                   stderr=DEVNULL).stdout.strip().splitlines()
    installed_packages_names = []
    for line in installed_packages_lines:
        name = line.split()[0].strip()
        installed_packages_names.append(name)

    package_names = package_names[:]
    package_names.extend(installed_packages_names)
    package_names = list(set([utilities.strip_versioning_from_name(name) for name in package_names]))
    return_dict = {}

    while package_names:
        classify_dict = classifiy_packages_priv(package_names)
        return_dict.update(classify_dict)

        # get deps of classified packages
        deps = []
        for package in classify_dict.values():
            if isinstance(package, package_classes.ArchPackage):
                if package.make_depends is not None:
                    for dep in package.make_depends:
                        deps.append(dep)

                if package.check_depends is not None:
                    for dep in package.check_depends:
                        deps.append(dep)

                if package.depends is not None:
                    for dep in package.depends:
                        deps.append(dep)

        # search for unfulfilled deps
        pacman_query = "pacman -T '" + "' '".join(deps) + "'"
        subprocess_return = run(pacman_query, shell=True, universal_newlines=True, stdout=PIPE,
                                stderr=DEVNULL).stdout.strip().splitlines()

        # find packages to classify next
        package_names = []
        for line in subprocess_return:
            name = utilities.strip_versioning_from_name(line)
            if (name not in return_dict) and (name not in package_names):
                package_names.append(name)

    return return_dict


def classifiy_packages_priv(package_names):
    """
    Classifies package_names.
    :param package_names:   The names of the packages to classify in a list
    :return:                Dict containing the classified packages.
                            {
                                "name1": package1,
                                "name2": package2,
                                ...
                            }
    """

    return_dict = {}
    # remove versioning from names and duplicates
    package_names = list(set([utilities.strip_versioning_from_name(package_name) for package_name in package_names]))
    if not package_names:
        return return_dict

    # at this point all we know are named objects
    for package_name in package_names:
        return_dict[package_name] = package_classes.NamedObject(package_name)

    # search for repo packages
    to_classify_names = package_names[:]
    expac_query = "expac -S '%n %v %H:%D:%P' " + " ".join(package_names)
    expac_result = run(expac_query, shell=True, stdout=PIPE, stderr=DEVNULL,
                       universal_newlines=True).stdout.strip().splitlines()

    for line in expac_result:
        name = line.split()[0].strip()
        version = line.split()[1].strip()
        rest = " ".join(line.split()[2:])
        conflicts = rest.split(":")[0].split()
        depends = rest.split(":")[1].split()
        provides = rest.split(":")[2].split()
        return_dict[name] = package_classes.RepoPackage(name=name, upstream_version=version, conflicts=conflicts,
                                                        depends=depends, provides=provides)
        to_classify_names.remove(name)

    to_classify_names_dup = to_classify_names[:]
    try:
        # search for aur packages
        aur_info_results = aur_utilities.get_aur_info(to_classify_names)["results"]
        for package_dict in aur_info_results:
            name = package_dict["Name"]

            kwargs_dict = {"name": name, "upstream_version": package_dict["Version"],
                           "make_depends": package_dict.get("MakeDepends", []),
                           "check_depends": package_dict.get("CheckDepends", []),
                           "depends": package_dict.get("Depends", []), "provides": package_dict.get("Provides", []),
                           "conflicts": package_dict.get("Conflicts", []),
                           "package_base_name": package_dict["PackageBase"]}

            if aur_utilities.is_devel(name):
                return_dict[name] = package_classes.DevelPackage(**kwargs_dict)
            else:
                return_dict[name] = package_classes.AURPackage(**kwargs_dict)

            to_classify_names.remove(name)

    except KeyError:
        logging.error("Malformed AurJson answer for %s", str(to_classify_names_dup), exc_info=True)
        raise InvalidInput()

    # get versions of installed packages
    installed_packages_names = []
    for package_name in return_dict:
        if package_name not in to_classify_names:
            installed_packages_names.append(package_name)

    if installed_packages_names:
        expac_query = "expac -Q '%n %v' " + " ".join(installed_packages_names)
        expac_result = run(expac_query, shell=True, stdout=PIPE, stderr=DEVNULL,
                           universal_newlines=True).stdout.strip().splitlines()

        for line in expac_result:
            name = line.split()[0].strip()
            version = line.split()[1].strip()
            package = return_dict[name]
            package.installed_version = version

    return return_dict


def get_installed_aur_packages(packages_dict):
    return_list = []

    for package_name in packages_dict:
        package = packages_dict[package_name]
        if isinstance(package, package_classes.AURPackage):
            if package.installed_version is not None:
                return_list.append(package)

    return return_list


def what_to_install_with_deps(packages_to_install, packages_dict):
    return_list = packages_to_install[:]

    # get deps of packages
    deps = []
    for package in return_list:
        if isinstance(package, package_classes.ArchPackage):
            if package.make_depends is not None:
                for dep in package.make_depends:
                    deps.append(dep)

            if package.check_depends is not None:
                for dep in package.check_depends:
                    deps.append(dep)

            if package.depends is not None:
                for dep in package.depends:
                    deps.append(dep)

    while deps:
        # search for unfulfilled deps
        pacman_query = "pacman -T '" + "' '".join(deps) + "'"
        subprocess_return = run(pacman_query, shell=True, universal_newlines=True, stdout=PIPE,
                                stderr=DEVNULL).stdout.strip().splitlines()
        next_packages = []

        for line in subprocess_return:
            name = utilities.strip_versioning_from_name(line)
            if (name not in return_list) and (name not in next_packages):
                next_packages.append(name)
                return_list.append(packages_dict[name])

        # get deps of packages
        deps = []
        for package in next_packages:
            if isinstance(package, package_classes.ArchPackage):
                if package.make_depends is not None:
                    for dep in package.make_depends:
                        deps.append(dep)

                if package.check_depends is not None:
                    for dep in package.check_depends:
                        deps.append(dep)

                if package.depends is not None:
                    for dep in package.depends:
                        deps.append(dep)

    return return_list


def check_versioning_and_conflicts(packages_to_change, packages_dict):
    """
    Checks versioning and conflicts
    Returns nothing, but throws an Exception in case of an unfulfilled dep.
    Conflicts are just logged (have fun pacman)
    :param packages_to_change:  A list containing the packages that will be changed, which means that the latest
                                version available gets installed, should be the return value of which_packages_need_changing
                                + packages you want to update
    :param packages_dict:       Return value of classifiy_packages_fully
    """
    packages_to_change_dict = {}
    for package in packages_to_change:
        packages_to_change_dict[package.name] = package
    packages_to_change = packages_to_change_dict

    all_packages = copy.deepcopy(packages_dict)
    all_packages.update(packages_to_change)
    for package_to_change in packages_to_change.values():
        if isinstance(package_to_change, package_classes.ArchPackage):
            package_to_change.installed_version = package_to_change.latest_version_available()

    # installed packages
    expac_query = "expac -Q '%n %v %H:%D:%P'"
    expac_result = run(expac_query, shell=True, stdout=PIPE, stderr=DEVNULL,
                       universal_newlines=True).stdout.strip().splitlines()

    for line in expac_result:
        name = line.split()[0].strip()
        version = line.split()[1].strip()
        rest = " ".join(line.split()[2:])
        conflicts = rest.split(":")[0].split()
        depends = rest.split(":")[1].split()
        provides = rest.split(":")[2].split()
        if name not in all_packages:
            all_packages[name] = package_classes.ArchPackage(name=name, installed_version=version, conflicts=conflicts,
                                                             depends=depends, provides=provides)

    deps_pool = []
    for package_name in all_packages:
        package = all_packages[package_name]
        if isinstance(package, package_classes.ArchPackage):
            for conflict in package.conflicts:
                if (conflict in all_packages) and (conflict != package_name):
                    logging.info("Conflict between %s and %s", package_name, conflict)
                    # raise InvalidInput()

            if package.make_depends is not None:
                for dep in package.make_depends:
                    if dep not in deps_pool:
                        deps_pool.append(dep)

            if package.check_depends is not None:
                for dep in package.check_depends:
                    if dep not in deps_pool:
                        deps_pool.append(dep)

            if package.depends is not None:
                for dep in package.depends:
                    if dep not in deps_pool:
                        deps_pool.append(dep)

    for dep in deps_pool:
        dep_name, dep_cmp, dep_version = utilities.split_name_with_versioning(dep)
        if (dep_name not in all_packages) or (not isinstance(all_packages[dep_name], package_classes.ArchPackage)):
            if run("pacman -Sp " + dep_name, shell=True, stdout=DEVNULL, stderr=DEVNULL).returncode != 0:
                logging.error("Dep %s not fulfilled", dep)
                raise InvalidInput()

        else:
            if dep_cmp != "":
                if not utilities.version_comparison(all_packages[dep_name].installed_version, dep_cmp, dep_version):
                    logging.error("Dep %s not fulfilled", dep)
                    raise InvalidInput()


def split_packages(packages_to_install):
    aur_to_return = []
    repo_to_return = []

    for package in packages_to_install:
        if isinstance(package, package_classes.AURPackage):
            aur_to_return.append(package)
        else:
            repo_to_return.append(package)

    return aur_to_return, repo_to_return


def order_aur_packages(aur_packages_to_install):
    def is_ready(package, packages_left):
        all_deps = []
        if package.make_depends is not None:
            all_deps.extend(package.make_depends)
        if package.check_depends is not None:
            all_deps.extend(package.check_depends)
        if package.depends is not None:
            all_deps.extend(package.depends)

        all_deps = list(set([utilities.strip_versioning_from_name(name) for name in all_deps]))
        packages_names = [package.name for package in packages_left]
        for dep in all_deps:
            if dep in packages_names:
                return False

        return True

    packages_to_order = aur_packages_to_install[:]
    ordered_packages = []

    while packages_to_order:
        for current_package in packages_to_order[:]:
            # all dependencies fulfilled
            if is_ready(current_package, packages_to_order):
                packages_to_order.remove(current_package)
                ordered_packages.append(current_package)
                break
        else:
            logging.error("cycle in deps")
            raise InvalidInput()

    return ordered_packages
