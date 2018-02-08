from utilities import strip_versioning_from_name, version_comparison, ask_user
from own_exceptions import InvalidInput, ConnectionProblem
import logging
import os
from subprocess import run, PIPE, DEVNULL
from package_utilites import call_pacman
from parse_args import args_to_string
from copy import deepcopy


class NamedObject:
    """
    Base class.

    Things only defined by name.
    """

    def __init__(self, name):
        self.name = strip_versioning_from_name(name)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.__dict__)

    def installed_in_latest_version(self):
        return False


class ArchPackage(NamedObject):
    """
    Arch Linux Package.

    Name
    Installed version
    Upstream version
    Make Dependencies
    Check Dependencies
    Dependencies
    Provides
    Conflicts
    """

    def latest_version_available(self):
        if self.installed_in_latest_version():
            return self.installed_version
        else:
            return self.upstream_version

    def installed_in_latest_version(self):
        """
        If this package is installed in the latest version available

        :return:    True if this package is installed in the latest version available
                    False otherwise
        """

        if self.installed_version is None:
            return False

        return version_comparison(self.installed_version, ">=", self.upstream_version)

    def __init__(self, name, installed_version=None, upstream_version=None, make_depends=None, check_depends=None,
                 depends=None, provides=None, conflicts=None):
        super().__init__(name)
        self.installed_version = installed_version
        self.upstream_version = upstream_version
        self.make_depends = make_depends
        self.check_depends = check_depends
        self.depends = depends
        self.provides = provides
        self.conflicts = conflicts


class RepoPackage(ArchPackage):
    """
    Arch Linux Repository Package.

    Name
    Installed version
    Upstream version
    Make Dependencies
    Check Dependencies
    Dependencies
    Provides
    Conflicts
    """

    def __init__(self, name, installed_version=None, upstream_version=None, make_depends=None, check_depends=None,
                 depends=None, provides=None, conflicts=None):
        super().__init__(name, installed_version, upstream_version, make_depends, check_depends, depends, provides,
                         conflicts)


class AURPackage(ArchPackage):
    """
    Arch Linux AUR Package

    Name
    Installed version
    Upstream version
    Make Dependencies
    Check Dependencies
    Dependencies
    Provides
    Conflicts
    Package Base Name
    """

    # default editor path
    default_editor_path = os.environ.get("EDITOR", os.path.join("usr", "bin", "nano"))
    # directory of the cache
    cache_dir = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.expanduser(os.path.join("~", ".cache"))),
                             "aurman")

    def install(self, args_as_dict):
        package_dir = os.path.join(AURPackage.cache_dir, self.package_base_name)
        # get name of install file
        build_version = self.version_from_srcinfo()
        files_in_build_dir = [f for f in os.listdir(package_dir) if os.path.isfile(os.path.join(package_dir, f))]
        install_file = None
        for file in files_in_build_dir:
            if file.startswith(self.name + "-" + build_version) and ".pkg." in \
                    file.split(self.name + "-" + build_version)[1]:
                install_file = file
                break

        if install_file is None:
            logging.error("package file of %s not available", str(self.name))
            raise InvalidInput()

        # install
        args = deepcopy(args_as_dict)
        args[''] = [install_file]
        call_pacman('U', args_to_string(args), package_dir)

    def build(self):
        # check if build needed
        build_version = self.version_from_srcinfo()
        package_dir = os.path.join(AURPackage.cache_dir, self.package_base_name)
        files_in_build_dir = [f for f in os.listdir(package_dir) if os.path.isfile(os.path.join(package_dir, f))]
        install_file = None
        for file in files_in_build_dir:
            if file.startswith(self.name + "-" + build_version) and ".pkg." in \
                    file.split(self.name + "-" + build_version)[1]:
                install_file = file
                break

        if install_file is None:
            if run("makepkg -sc --noconfirm", shell=True, cwd=package_dir).returncode != 0:
                logging.error("build of %s failed", str(self.name))
                raise InvalidInput()

    def version_from_srcinfo(self):
        """
        Returns the version from the srcinfo
        Exceptions: Exceptions.InvalidInput
        :return:    The version read from the srcinfo
        """

        if self.package_base_name is None:
            logging.error("base package name of %s not known", str(self.name))
            raise InvalidInput()

        package_dir = os.path.join(AURPackage.cache_dir, self.package_base_name)
        if not os.path.isdir(package_dir):
            logging.error("package dir of %s does not exist", str(self.name))
            raise InvalidInput()

        srcinfo_all = run("makepkg --printsrcinfo", shell=True, stdout=PIPE, stderr=DEVNULL, cwd=package_dir,
                          universal_newlines=True)

        if srcinfo_all.returncode != 0:
            logging.error("reading from srcinfo of %s failed", str(self.name))
            raise InvalidInput()

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
            logging.info("version of %s must be there", str(self.name))
            raise InvalidInput()
        if pkgrel is not None:
            version += "-" + pkgrel

        return version

    def show_pkgbuild_install_files_to_user(self):
        """
        Lets the user review and edit unreviewed PKGBUILD and install files of this package
        """

        package_dir = os.path.join(AURPackage.cache_dir, self.package_base_name)
        git_aurman_dir = os.path.join(package_dir, ".git", "aurman")
        reviewed_file = os.path.join(git_aurman_dir, ".reviewed")

        # if package dir does not exist - abort
        if not os.path.isdir(package_dir):
            logging.error("Package dir of %s does not exist", self.name)
            raise InvalidInput()

        # if aurman dir does not exist - create
        if not os.path.isdir(git_aurman_dir):
            if run("install -dm700 '" + git_aurman_dir + "'", shell=True, stdout=DEVNULL,
                   stderr=DEVNULL).returncode != 0:
                logging.error("Creating git_aurman_dir of %s failed", self.name)
                raise InvalidInput()

        # if reviewed file does not exist - create
        if not os.path.isfile(reviewed_file):
            with open(reviewed_file, "w") as f:
                f.write("0")

        # if files have been reviewed
        with open(reviewed_file, "r") as f:
            to_review = f.read().strip() == "0"

        if not to_review:
            return

        # relevant files are PKGBUILD + .install files
        relevant_files = ["PKGBUILD"]
        files_in_pack_dir = [f for f in os.listdir(package_dir) if os.path.isfile(os.path.join(package_dir, f))]
        for file in files_in_pack_dir:
            if file.endswith(".install"):
                relevant_files.append(file)

        # check if there are changes, if there are, ask the user if he wants to see them
        for file in relevant_files:
            if os.path.isfile(os.path.join(git_aurman_dir, file)):
                if run("git diff --quiet '" + "' '".join([os.path.join(git_aurman_dir, file), file]) + "'", shell=True,
                       cwd=package_dir).returncode == 1:
                    if ask_user("Do you want to view the changes of " + file + " of " + self.name + " ?", False):
                        run("git diff --no-index '" + "' '".join([os.path.join(git_aurman_dir, file), file]) + "'",
                            shell=True, cwd=package_dir)
                        changes_seen = True
                    else:
                        changes_seen = False
                else:
                    changes_seen = False
            else:
                if ask_user("Do you want to view the changes of " + file + " of " + self.name + " ?", False):
                    run("git diff --no-index '" + "' '".join([os.path.join("/dev", "null"), file]) + "'", shell=True,
                        cwd=package_dir)

                    changes_seen = True
                else:
                    changes_seen = False

            # if the user wanted to see changes, ask, if he wants to edit the file
            if changes_seen:
                if ask_user("Do you want to edit " + file + "?", False):
                    if run(AURPackage.default_editor_path + " " + os.path.join(package_dir, file),
                           shell=True).returncode != 0:
                        logging.error("Editing %s failed", file)
                        raise InvalidInput()

        # if the user wants to use all files as they are now
        # copy all reviewed files to another folder for comparison of future changes
        if ask_user("Do you want to use the files as they are now?", True):
            with open(reviewed_file, "w") as f:
                f.write("1")

            for file in relevant_files:
                run("cp -f '" + "' '".join([file, os.path.join(git_aurman_dir, file)]) + "'", shell=True,
                    stdout=DEVNULL, stderr=DEVNULL, cwd=package_dir)

        else:
            logging.error("Files of %s are not okay", str(self.name))
            raise InvalidInput()

    def fetch_latest_pkgbuild_install_files(self):
        """
        Fetches the current git aur repo changes for this package
        In cache_dir/package_base_name/.git/aurman will be copies of the last reviewed PKGBUILD and .install files
        In cache_dir/package_base_name/.git/aurman/.reviewed will be saved if the current PKGBUILD and .install files have been reviewed
        """

        package_dir = os.path.join(AURPackage.cache_dir, self.package_base_name)
        git_aurman_dir = os.path.join(package_dir, ".git", "aurman")
        new_loaded = True

        # check if repo has ever been fetched
        if os.path.isdir(package_dir):
            if run("git fetch", shell=True, stdout=DEVNULL, stderr=DEVNULL, cwd=package_dir).returncode != 0:
                logging.error("git fetch of %s failed", self.name)
                raise ConnectionProblem()

            head = run("git rev-parse HEAD", shell=True, stdout=PIPE, universal_newlines=True,
                       cwd=package_dir).stdout.strip()
            u = run("git rev-parse @{u}", shell=True, stdout=PIPE, universal_newlines=True,
                    cwd=package_dir).stdout.strip()

            # if new sources available
            if head != u:
                if run("git reset --hard HEAD && git pull", shell=True, stdout=DEVNULL, stderr=DEVNULL,
                       cwd=package_dir).returncode != 0:
                    logging.error("sources of %s could not be fetched", self.name)
                    raise ConnectionProblem()
            else:
                new_loaded = False

        # repo has never been fetched
        else:
            if run("install -dm700 '" + package_dir + "'", shell=True, stdout=DEVNULL, stderr=DEVNULL).returncode != 0:
                logging.error("Creating package dir of %s failed", self.name)
                raise InvalidInput()

            # clone repo
            if run("git clone https://aur.archlinux.org/" + self.package_base_name + ".git", shell=True, stdout=DEVNULL,
                   stderr=DEVNULL, cwd=AURPackage.cache_dir).returncode != 0:
                logging.error("Cloning repo of %s failed", self.name)
                raise ConnectionProblem()

            # create git_aurman_dir
            if run("install -dm700 '" + git_aurman_dir + "'", shell=True, stdout=DEVNULL,
                   stderr=DEVNULL).returncode != 0:
                logging.error("Creating git_aurman_dir of %s failed", self.name)
                raise InvalidInput()

        # files have not yet been reviewed
        if new_loaded:
            with open(os.path.join(git_aurman_dir, ".reviewed"), "w") as f:
                f.write("0")

    def __init__(self, name, installed_version=None, upstream_version=None, make_depends=None, check_depends=None,
                 depends=None, provides=None, conflicts=None, package_base_name=None):
        super().__init__(name, installed_version, upstream_version, make_depends, check_depends, depends, provides,
                         conflicts)

        self.package_base_name = package_base_name


class DevelPackage(AURPackage):
    """
    Arch Linux AUR Development Package

    Name
    Installed version
    Upstream version
    Make Dependencies
    Check Dependencies
    Dependencies
    Provides
    Conflicts
    Package Base Name
    Development Version
    """

    def latest_version_available(self):
        super_val = super().latest_version_available()

        if self.devel_version is None:
            return super_val
        else:
            if version_comparison(self.devel_version, ">=", super_val):
                return self.devel_version
            else:
                return super_val

    def fetch_latest_sources(self, noedit):
        """
        Fetches the current sources of this package.
        devel packages only!
        Exceptions: Exceptions.ConnectionProblem,
                    Exceptions.InvalidInput
        """

        self.fetch_latest_pkgbuild_install_files()
        if not noedit:
            self.show_pkgbuild_install_files_to_user()

        package_dir = os.path.join(AURPackage.cache_dir, self.package_base_name)

        if run("makepkg -odc --noprepare --skipinteg", shell=True, cwd=package_dir).returncode != 0:
            logging.error("silent extraction of %s failed", str(self.name))
            raise InvalidInput()

        self.devel_version = self.version_from_srcinfo()

    def installed_in_latest_version(self):
        """
        If this package is installed in the latest version available

        :return:    True if this package is installed in the latest version available
                    False otherwise
        """

        if self.installed_version is None:
            return False

        super_val = super().installed_in_latest_version()

        if self.devel_version is None:
            return super_val
        else:
            return version_comparison(self.installed_version, ">=", self.devel_version)

    def __init__(self, name, installed_version=None, upstream_version=None, make_depends=None, check_depends=None,
                 depends=None, provides=None, conflicts=None, package_base_name=None, devel_version=None):
        super().__init__(name, installed_version, upstream_version, make_depends, check_depends, depends, provides,
                         conflicts, package_base_name)

        self.devel_version = devel_version
