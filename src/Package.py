import os
import Exceptions
import subprocess
import logging

import Utils

default_editor_path = os.path.join("usr", "bin", "nano")


class Package:
    # directory of the cache
    cache_dir = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.expanduser(os.path.join("~", ".cache"))),
                             "aurman")

    def __init__(self, name):
        # name of the package
        self.name = name.strip()
        # indicates if the package is a repo package or a group
        self.in_repo_or_group = None
        # indicates if the package is an aur package
        self.in_aur = None
        # indicates if the package is a development package
        self.is_devel = None
        # base name of the package (aur and devel packages only)
        self.package_base_name = None
        # if the package is installed
        self.installed = None
        # version of the installed package (installed packages only)
        self.installed_version = None
        # upstream version (repo packages only)
        self.upstream_version = None
        # version of the package in the aur (aur and devel packages only)
        self.aur_version = None
        # current version of the package (development packages only)
        self.devel_version = None
        # list of names of the dependencies (makedepends and depends, but for aur and devel packages only)
        self.dependencies = None
        # list of names of conflicts (aur and devel packages only)
        self.conflicts = None

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.__dict__)

    @staticmethod
    def install_repo_packages(explicit_packages, as_deps_packages, *args):
        """
        Installs repo packages and groups via pacman.
        Pass additional parameters for pacman via *args.

        Exception: Exceptions.InvalidInput

        :param explicit_packages:   Names of the packages that should be installed explicitly.
        :param as_deps_packages:    Names of the packages that should be installed as deps.
        :param args:                e.g. "--noconfirm", "--needed"
        """

        pacman_prefix = " ".join(args)

        if explicit_packages:
            if subprocess.run("sudo pacman " + pacman_prefix + " -S " + " ".join(explicit_packages),
                              shell=True).returncode != 0:
                logging.info("install of %s failed", str(explicit_packages))
                raise Exceptions.InvalidInput("install failed")

        if as_deps_packages:
            if subprocess.run("sudo pacman --needed --asdeps " + pacman_prefix + " -S " + " ".join(as_deps_packages),
                              shell=True).returncode != 0:
                logging.info("install of %s failed", str(as_deps_packages))
                raise Exceptions.InvalidInput("install failed")

    def install_package(self, *args):
        """
        Builds and installs the package via makepkg and pacman.
        Pass additional parameters for pacman via *args.

        Exceptions: Exceptions.InvalidInput,
                    Exceptions.ConnectionProblem

        :param args:    e.g. "--asdeps", "--needed"
        """

        pacman_prefix = " ".join(args)
        if self.package_base_name is None:
            logging.info("base package name not known")
            raise Exceptions.InvalidInput("base package name not known")

        package_dir = os.path.join(Package.cache_dir, self.package_base_name)

        # if new pkgbuild
        if self.fetch_pkgbuild():
            if not self.show_pkgbuild_to_user():
                logging.info("PKGBUILD not okay!")
                raise Exceptions.InvalidInput("PKGBUILD not okay!")

        # check if build needed
        build_version = self.version_from_srcinfo()
        files_in_build_dir = [f for f in os.listdir(package_dir) if os.path.isfile(os.path.join(package_dir, f))]
        install_file = None
        for file in files_in_build_dir:
            if file.startswith(self.name + "-" + build_version) and file.endswith(".pkg.tar"):
                install_file = file
                break

        if install_file is None:
            build_needed = True
        else:
            build_needed = False

        # build
        if build_needed:
            if subprocess.run("makepkg -Cc --noconfirm", shell=True, cwd=package_dir).returncode != 0:
                logging.info("build failed")
                raise Exceptions.InvalidInput("build failed")

            # get name of install file
            build_version = self.version_from_srcinfo()
            files_in_build_dir = [f for f in os.listdir(package_dir) if os.path.isfile(os.path.join(package_dir, f))]
            install_file = None
            for file in files_in_build_dir:
                if file.startswith(self.name + "-" + build_version) and file.endswith(".pkg.tar"):
                    install_file = file
                    break

            if install_file is None:
                logging.info("install file not available")
                raise Exceptions.InvalidInput("install file not available")

        # install
        if subprocess.run("sudo pacman " + pacman_prefix + " -U " + install_file, shell=True,
                          cwd=package_dir).returncode != 0:
            logging.info("install failed")
            raise Exceptions.InvalidInput("install failed")

    @staticmethod
    def is_any_conflict(packages):
        """
        Checks if there are conflicts between the packages

        :param packages:    Concrete instances of the packages
        :return:    Tuple:
                    First item: True if there is a conflict, False otherwise
                    Second item: Name of the first package with conflict
                    Third item: Name of the second package with conflict
        """

        conflict_pool = {}
        for package in packages:
            if package.conflicts is not None:
                conflict_pool[package.name] = [Utils.strip_versioning(conflict) for conflict in package.conflicts]

        for package in packages:
            for key in conflict_pool:
                if package.name in conflict_pool[key]:
                    return True, package.name, key

        return False, "", ""

    def ready_to_install(self, not_yet_installed_packages):
        """
        If the package is ready to install, which means that there
        are no unfulfilled dependencies.

        Exception: Exceptions.InvalidInput


        :param not_yet_installed_packages: names of not yet installed packages
        :return:    True in case it is ready for install, False otherwise
        """

        if self.dependencies is None:
            logging.info("dependencies not known")
            raise Exceptions.InvalidInput("dependencies not known")

        for dep in self.dependencies:
            if Utils.strip_versioning(dep) in not_yet_installed_packages:
                return False

        return True

    def version_from_srcinfo(self):
        """
        Returns the version from the srcinfo

        Exceptions: Exceptions.InvalidInput

        :return:    The version read from the srcinfo
        """

        if self.package_base_name is None:
            logging.info("base package name not known")
            raise Exceptions.InvalidInput("base package name not known")

        package_dir = os.path.join(Package.cache_dir, self.package_base_name)
        if not os.path.isdir(package_dir):
            logging.info("package dir does not exist")
            raise Exceptions.InvalidInput("package dir does not exist")

        srcinfo_all = subprocess.run("makepkg --printsrcinfo", shell=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, cwd=package_dir, universal_newlines=True)

        if srcinfo_all.returncode != 0:
            logging.info("reading from srcinfo failed")
            raise Exceptions.InvalidInput("reading from srcinfo failed")

        src_lines = srcinfo_all.stdout.strip().splitlines()
        pkgver = None
        pkgrel = None
        epoch = None
        for line in src_lines:
            if "pkgver =" in line:
                pkgver = line.split("=")[1].strip()
            elif "pkgrel =" in line:
                pkgrel = line.split("=")[1].strip()
            elif "epoch =" in line:
                epoch = line.split("=")[1].strip()

        version = ""
        if epoch is not None:
            version += epoch + ":"
        if pkgver is not None:
            version += pkgver
        else:
            logging.info("version must be there")
            raise Exceptions.InvalidInput("version must be there")
        if pkgrel is not None:
            version += "-" + pkgrel

        return version

    def fetch_current_sources(self):
        """
        Fetches the current sources of this package.
        devel packages only!

        Exceptions: Exceptions.ConnectionProblem,
                    Exceptions.InvalidInput

        """

        if not self.is_devel:
            logging.info("Not a devel package")
            raise Exceptions.InvalidInput("Not a devel package")

        # if new pkgbuild
        if self.fetch_pkgbuild():
            if not self.show_pkgbuild_to_user():
                logging.info("PKGBUILD not okay!")
                raise Exceptions.InvalidInput("PKGBUILD not okay!")

        package_dir = os.path.join(Package.cache_dir, self.package_base_name)

        if subprocess.run("makepkg -odc --noprepare --skipinteg", shell=True, cwd=package_dir).returncode != 0:
            logging.info("silent extraction failed")
            raise Exceptions.InvalidInput("silent extraction failed")

        self.devel_version = self.version_from_srcinfo()

    def show_pkgbuild_to_user(self):
        """
        Asks if the user wants to see/edit the PKGBUILD.
        If the user wants to, shows the PKGBUILD.
        Finally asks, if the PKGBUILD is ready to use.

        Exception: Exceptions.InvalidInput

        :return:    If the PKGBUILD is ready to use.
                    True in case it is, False otherwise
        """
        global default_editor_path

        if self.package_base_name is None:
            logging.info("base package name not known")
            raise Exceptions.InvalidInput("base package name not known")

        pkgbuild_path = os.path.join(Package.cache_dir, self.package_base_name, "PKGBUILD")

        if not os.path.isfile(pkgbuild_path):
            logging.info("PKGBUILD not available")
            raise Exceptions.InvalidInput("PKGBUILD not available")

        if Utils.ask_user("Do you want to edit the PKGBUILD of " + self.name + "?", False):
            editor_path = os.environ.get("EDITOR", default_editor_path)
            if subprocess.run(editor_path + " " + pkgbuild_path, shell=True).returncode != 0:
                logging.info("Editing the PKGBUILD failed")
                raise Exceptions.InvalidInput("Editing the PKGBUILD failed")

        return Utils.ask_user("Do you want to use the PKGBUILD?", True)

    def is_group(self):
        """
        Checks if the package is a group instead

        :return:    True if group, False otherwise
        """
        if not self.in_repo_or_group:
            return False

        if self.upstream_version is None:
            return True
        else:
            return False

    def newest_version_available(self):
        """
        Returns the newest version available for this package

        Exception:  Exceptions.InvalidInput

        :return:    The newest version available
        """

        # maybe there is a nicer way, but those ifs do it for now
        if self.in_repo_or_group:
            if self.is_group():
                logging.info("Package is a group")
                raise Exceptions.InvalidInput("Package is a group")

            if not self.installed:
                return self.upstream_version

            if Utils.compare_versions(self.installed_version, self.upstream_version) >= 0:
                return self.installed_version
            else:
                return self.upstream_version

        if self.in_aur:
            if not self.installed:
                return self.aur_version

            if Utils.compare_versions(self.installed_version, self.aur_version) >= 0:
                return self.installed_version
            else:
                return self.aur_version

        if self.is_devel:
            if not self.installed:
                curr_biggest = self.aur_version
            else:
                if Utils.compare_versions(self.installed_version, self.aur_version) >= 0:
                    curr_biggest = self.installed_version
                else:
                    curr_biggest = self.aur_version

            if self.devel_version is None:
                return curr_biggest

            if Utils.compare_versions(curr_biggest, self.devel_version) >= 0:
                return curr_biggest
            else:
                return self.devel_version

        logging.info("Package not valid")
        raise Exceptions.InvalidInput("Package not valid")

    def is_installed_and_latest(self):
        """
        Checks if the package is installed
        and if it is, if the version is the newest available

        Exception:  Exceptions.InvalidInput


        :return:    True in case it is, False otherwise
        """
        if self.installed is None:
            logging.info("Installed status not available")
            raise Exceptions.InvalidInput("Installed status not available")

        if not self.installed:
            return False

        if self.in_repo_or_group:
            return Utils.compare_versions(self.installed_version, self.upstream_version) >= 0
        elif self.in_aur:
            return Utils.compare_versions(self.installed_version, self.aur_version) >= 0
        else:
            assert self.is_devel
            if self.devel_version is not None:
                return Utils.compare_versions(self.installed_version, self.devel_version) >= 0
            else:
                return Utils.compare_versions(self.installed_version, self.aur_version) >= 0

    def fetch_pkgbuild(self):
        """
        Fetches the current PKGBUILD of the package (aur and devel packages only)

        Exceptions: Exceptions.ConnectionProblem,
                    Exceptions.InvalidInput

        :return:    True if a new PKGBUILD has been fetched, False otherwise
        """
        if self.package_base_name is None:
            logging.info("base package name not known")
            raise Exceptions.InvalidInput("base package name not known")

        if not os.path.exists(Package.cache_dir):
            if subprocess.run("install -dm700 '" + Package.cache_dir + "'", shell=True, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode != 0:
                logging.info("cache dir could not be created")
                raise Exceptions.InvalidInput("cache dir could not be created")

        package_dir = os.path.join(Package.cache_dir, self.package_base_name)

        if not os.path.exists(package_dir):
            if subprocess.run("git clone https://aur.archlinux.org/" + self.package_base_name + ".git", shell=True,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              cwd=Package.cache_dir).returncode != 0:
                logging.info("git clone not completed")
                raise Exceptions.ConnectionProblem("git clone not completed")
            else:
                return True

        if not os.path.isdir(package_dir):
            logging.info("package dir not available")
            raise Exceptions.InvalidInput("package dir not available")

        if subprocess.run("git fetch", shell=True, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, cwd=package_dir).returncode != 0:
            logging.info("git fetch failed")
            raise Exceptions.ConnectionProblem("git fetch failed")

        head = subprocess.run("git rev-parse HEAD", shell=True, stdout=subprocess.PIPE,
                              universal_newlines=True, cwd=package_dir).stdout.strip()
        u = subprocess.run("git rev-parse @{u}", shell=True, stdout=subprocess.PIPE,
                           universal_newlines=True, cwd=package_dir).stdout.strip()

        if head != u:
            new_pkgbuild_fetched = True

            if subprocess.run("git reset --hard HEAD && git pull", shell=True, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, cwd=package_dir).returncode != 0:
                logging.info("pkgbuild could not be fetched")
                raise Exceptions.ConnectionProblem("pkgbuild could not be fetched")
        else:
            new_pkgbuild_fetched = False

        logging.debug("pkgbuild of %s fetched without errors", str(self.name))
        return new_pkgbuild_fetched

    @staticmethod
    def retrieve_all_packages_information(names, known_not_repo=False):
        """
        Retrieves information for packages. Includes classifying by classify_packages_complete

        Exceptions: Exceptions.ConnectionProblem,
                    Exceptions.InvalidInput

        :param names:   The names of the packages to receive information for
        :param known_not_repo: if the names are known not to be in repo
        :return:    First item of the tuple:    Dict containing names of the packages as keys
                                                and the concrete objects of the packages as values

                    Second item of the tuple:   Return dict of classify_packages_complete

                    (
                        {
                            "package1": "package1",   # object of the package as value
                            "package2": "package2",   # object of the package as value
                            ...
                        },
                        {
                            "repo_or_group": ["package1", ...],
                            "aur": ["package1", ...], # aur packages which are not development packages
                            "devel": ["package1", ...], # development packages, are always also aur packages
                            "not_valid": ["package1", ...]
                        }
                    )
        """

        our_dict = {}
        retrv_dict = Package.classify_packages_complete(names, known_not_repo)
        for key in retrv_dict:
            packages = retrv_dict[key]
            for package in packages:
                our_dict[package.name] = package

        return our_dict, retrv_dict

    @staticmethod
    def classify_packages(names, known_not_repo=False):
        """
        Classifies packages. "Repo or group", "AUR but not devel", "Devel" or "not valid".
        Also creates concrete instances for the packages and fills in all information except for
        "self.devel_version".

        Exceptions: Exceptions.ConnectionProblem,
                    Exceptions.InvalidInput

        :param names:   list of names of the packages to classify
        :param known_not_repo: if the names are known not to be in repo
        :return:    a dict containing the classified packages

                    {
                        "repo_or_group": ["package1", ...],
                        "aur": ["package1", ...], # aur packages which are not development packages
                        "devel": ["package1", ...], # development packages, are always also aur packages
                        "not_valid": ["package1", ...]
                    }
        """

        # remove versioning from input names and remove duplicates
        new_names = list(set([Utils.strip_versioning(name) for name in names]))
        return_dict = {"repo_or_group": [], "aur": [], "devel": [], "not_valid": []}

        # we do not know more than that they are not in repo
        if known_not_repo:
            to_classify = []
            for name in new_names:
                new_package = Package(name)
                new_package.in_repo_or_group = False
                to_classify.append(new_package)

        # we do not know anything
        else:
            if new_names:
                expac_query = "expac -S '%n %v' " + " ".join(new_names)
                result_lines = subprocess.run(expac_query, shell=True, stdout=subprocess.PIPE,
                                              universal_newlines=True).stdout.strip().splitlines()
            else:
                result_lines = []

            # every line represents a repo package
            for line in result_lines:
                name = line.split()[0]
                version = line.split()[1]
                new_package = Package(name)
                new_package.in_repo_or_group = True
                new_package.in_aur = False
                new_package.is_devel = False
                new_package.upstream_version = version
                return_dict["repo_or_group"].append(new_package)
                new_names.remove(name)

            # all not yet classified packages
            to_classify = [Package(name) for name in new_names]

            for package in to_classify[:]:
                # if package is group
                package.in_repo_or_group = subprocess.run("expac -Sg '' " + package.name, shell=True,
                                                          stdout=subprocess.DEVNULL).returncode == 0

                if package.in_repo_or_group:
                    package.in_aur = False
                    package.is_devel = False
                    return_dict["repo_or_group"].append(package)
                    to_classify.remove(package)

        # fetch aur info to classify left packages
        aur_info_dict = Utils.get_aur_info([package.name for package in to_classify])
        for package in to_classify[:]:
            if package.name not in aur_info_dict:
                package.in_aur = False
                package.is_devel = False
                return_dict["not_valid"].append(package)
                continue
            elif Utils.is_devel(package.name):
                package.is_devel = True
                package.in_aur = False
                return_dict["devel"].append(package)
            else:
                package.in_aur = True
                package.is_devel = False
                return_dict["aur"].append(package)

            package_dict = aur_info_dict[package.name]
            package.package_base_name = package_dict["PackageBase"]
            package.aur_version = package_dict["Version"]
            package.conflicts = package_dict["Conflicts"]
            package.dependencies = package_dict["Depends"]
            package.dependencies.extend(package_dict["MakeDepends"])

        # check if packages are installed and if so, which version
        dummy_dict = {}
        valid_packages = return_dict["aur"][:]
        valid_packages.extend(return_dict["devel"])
        valid_packages.extend(return_dict["repo_or_group"])

        for package in valid_packages:
            dummy_dict[package.name] = package

        valid_packages_names = [package.name for package in valid_packages]
        if valid_packages_names:
            expac_query = "expac -Q '%n %v' " + " ".join(valid_packages_names)
            result_lines = subprocess.run(expac_query, shell=True, stdout=subprocess.PIPE,
                                          universal_newlines=True).stdout.strip().splitlines()
        else:
            result_lines = []

        for line in result_lines:
            name = line.split()[0]
            version = line.split()[1]
            curr_package = dummy_dict[name]
            curr_package.installed = True
            curr_package.installed_version = version
            del dummy_dict[name]

        for package in dummy_dict.values():
            package.installed = False

        logging.debug("%s parsed without errors", str(names))
        return return_dict

    @staticmethod
    def classify_packages_complete(names, known_not_repo=False):
        """
        Classifies packages. "Repo or group", "AUR but not devel", "Devel" or "not valid".
        Also creates concrete instances for the packages and fills in all information except for
        "self.devel_version".

        In contrast to "classify_packages" - Does this until all dependencies of aur and devel packages
        are also classified.

        Exceptions: Exceptions.ConnectionProblem,
                    Exceptions.InvalidInput

        :param names:   list of names of the packages to classify
        :param known_not_repo: if the names are known not to be in repo
        :return:    a dict containing the classified packages

                    {
                        "repo_or_group": ["package1", ...],
                        "aur": ["package1", ...], # aur packages which are not development packages
                        "devel": ["package1", ...], # development packages, are always also aur packages
                        "not_valid": ["package1", ...]
                    }
        """
        classified_names = []
        to_classify_names = names
        return_dict = {"repo_or_group": [], "aur": [], "devel": [], "not_valid": []}

        while to_classify_names:
            classified_dict = Package.classify_packages(to_classify_names, known_not_repo)
            for key in classified_dict:
                return_dict[key].extend(classified_dict[key])
                package_list = classified_dict[key]
                for package in package_list:
                    classified_names.append(package.name)

            aur_and_devel = classified_dict["aur"]
            aur_and_devel.extend(classified_dict["devel"])
            to_classify_names = []
            for package in aur_and_devel:
                if not package.is_installed_and_latest() or package.is_devel:
                    for dep in package.dependencies:
                        if Utils.strip_versioning(dep) not in classified_names:
                            to_classify_names.append(dep)

        logging.debug("%s parsed without errors", str(names))
        return return_dict
