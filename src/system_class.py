from typing import Sequence, List
from package_class import Package, PossibleTypes
from utilities import strip_versioning_from_name, split_name_with_versioning, version_comparison
import logging
from own_exceptions import InvalidInput


class System:
    def __init__(self, packages: Sequence['Package']):
        self.all_packages_dict = {}  # names as keys and packages as values
        self.repo_packages_list = []  # list containing the repo packages
        self.aur_packages_list = []  # list containing the aur but not devel packages
        self.devel_packages_list = []  # list containing the aur devel packages
        self.not_repo_not_aur_packages_list = []  # list containing the packages that are neither repo nor aur packages

        # reverse dict for finding providings. names of providings as keys and providing packages as values in lists
        self.provides_dict = {}
        # same for conflicts
        self.conflicts_dict = {}

        self.append_packages(packages)

    def append_packages(self, packages: Sequence['Package']):
        """
        Appends packages to this system.

        :param packages:    The packages to append in a sequence
        """
        for package in packages:
            if package.name in self.all_packages_dict:
                logging.error("Package {} already known".format(package))
                raise InvalidInput()

            self.all_packages_dict[package.name] = package

            if package.type_of is PossibleTypes.REPO_PACKAGE:
                self.repo_packages_list.append(package)
            elif package.type_of is PossibleTypes.AUR_PACKAGE:
                self.aur_packages_list.append(package)
            elif package.type_of is PossibleTypes.DEVEL_PACKAGE:
                self.devel_packages_list.append(package)
            else:
                assert package.type_of is PossibleTypes.PACKAGE_NOT_REPO_NOT_AUR
                self.not_repo_not_aur_packages_list.append(package)

        self.__append_to_x_dict(packages, 'provides')
        self.__append_to_x_dict(packages, 'conflicts')

    def __append_to_x_dict(self, packages: Sequence['Package'], dict_name: str):
        dict_to_append_to = getattr(self, "{}_dict".format(dict_name))

        for package in packages:
            relevant_package_values = getattr(package, dict_name)

            for relevant_value in relevant_package_values:
                value_name = strip_versioning_from_name(relevant_value)
                if value_name in dict_to_append_to:
                    dict_to_append_to[value_name].append(package)
                else:
                    dict_to_append_to[value_name] = [package]

    def provided_by(self, dep: str) -> List['Package']:
        """
        Providers for the dep

        :param dep:     The dep to be provided
        :return:        List containing the providing packages
        """

        dep_name, dep_cmp, dep_version = split_name_with_versioning(dep)
        return_list = []

        if dep_name in self.all_packages_dict:
            package = self.all_packages_dict[dep_name]
            if dep_cmp == "":
                return_list.append(package)
            elif version_comparison(package.version, dep_cmp, dep_version):
                return_list.append(package)

        if dep_name in self.provides_dict:
            possible_packages = self.provides_dict[dep_name]
            for package in possible_packages:

                if package in return_list:
                    continue

                for provide in package.provides:
                    provide_name, provide_cmp, provide_version = split_name_with_versioning(provide)

                    if provide_name != dep_name:
                        continue

                    if dep_cmp == "":
                        return_list.append(package)
                    elif (provide_cmp == "=" or provide_cmp == "==") and version_comparison(provide_version, dep_cmp,
                                                                                            dep_version):
                        return_list.append(package)
                    elif (provide_cmp == "") and version_comparison(package.version, dep_cmp, dep_version):
                        return_list.append(package)

        return return_list

    def conflicting_with(self, package: 'Package') -> List['Package']:
        """
        Returns the packages conflicting with "package"

        :param package:     The package to check for conflicts with
        :return:            List containing the conflicting packages
        """
        name = package.name
        version = package.version

        return_list = []

        if name in self.all_packages_dict:
            possible_conflict_package = self.all_packages_dict[name]
            if version != possible_conflict_package.version:
                return_list.append(possible_conflict_package)

        if name in self.conflicts_dict:
            possible_conflict_packages = self.conflicts_dict[name]
            for possible_conflict_package in possible_conflict_packages:

                if possible_conflict_package in return_list:
                    continue

                for conflict in possible_conflict_package.conflicts:
                    conflict_name, conflict_cmp, conflict_version = split_name_with_versioning(conflict)

                    if conflict_name != name:
                        continue

                    if conflict_cmp == "":
                        return_list.append(possible_conflict_package)
                    elif version_comparison(version, conflict_cmp, conflict_version):
                        return_list.append(possible_conflict_package)

        return return_list
