from typing import Sequence, List, Tuple, Union
from enum import Enum, auto
from copy import deepcopy
from wrappers import expac
from aur_utilities import is_devel, get_aur_info
from system_class import System


class PossibleTypes(Enum):
    REPO_PACKAGE = auto()
    AUR_PACKAGE = auto()
    DEVEL_PACKAGE = auto()
    PACKAGE_NOT_REPO_NOT_AUR = auto()


class Package:
    @staticmethod
    def user_input_to_categories(user_input: Sequence[str]) -> Tuple[Sequence[str], Sequence[str]]:
        """
        Categorizes user input in: For our AUR helper and for pacman

        :param user_input:  A sequence containing the user input as str
        :return:            Tuple containing two elements
                            First item: List containing the user input for our AUR helper
                            Second item: List containing the user input for pacman
        """
        for_us = []
        for_pacman = []

        found_in_aur_names = set([package.name for package in Package.get_packages_from_aur(user_input)])
        for _user_input in user_input:
            if _user_input in found_in_aur_names:
                for_us.append(_user_input)
            else:
                for_pacman.append(_user_input)

        return for_us, for_pacman

    @staticmethod
    def get_packages_from_aur(packages_names: Sequence[str]) -> List['Package']:
        """
        Generates and returns packages from the aur.
        see: https://wiki.archlinux.org/index.php/Arch_User_Repository

        :param packages_names:  The names of the packages to generate.
                                May not be empty.
        :return:                List containing the packages
        """
        aur_return = get_aur_info(packages_names)

        return_list = []

        for package_dict in aur_return:
            name = package_dict['Name']

            to_expand = {
                'name': name,
                'version': package_dict['Version'],
                'depends': package_dict.get('Depends', []),
                'conflicts': package_dict.get('Conflicts', []),
                'optdepends': package_dict.get('OptDepends', []),
                'provides': package_dict.get('Provides', []),
                'replaces': package_dict.get('Replaces', []),
                'pkgbase': package_dict['PackageBase'],
                'makedepends': package_dict.get('MakeDepends', []),
                'checkdepends': package_dict.get('CheckDepends', [])
            }

            if is_devel(name):
                to_expand['type_of'] = PossibleTypes.DEVEL_PACKAGE
            else:
                to_expand['type_of'] = PossibleTypes.AUR_PACKAGE

            return_list.append(Package(**to_expand))

        return return_list

    @staticmethod
    def get_packages_from_expac(expac_operation: str, packages_names: Sequence[str], packages_type: PossibleTypes) -> \
            List['Package']:
        """
        Generates and returns packages from an expac query.
        see: https://github.com/falconindy/expac

        :param expac_operation:     The expac operation. "-S" or "-Q".
        :param packages_names:      The names of the packages to generate.
                                    May also be empty, so that all packages are being returned.
        :param packages_type:       The type of the packages. PossibleTypes Enum value
        :return:                    List containing the packages
        """
        if "Q" in expac_operation:
            formatting = list("nvDHNoPRew")
        else:
            assert "S" in expac_operation
            formatting = list("nvDHNoPRe")

        expac_return = expac(expac_operation, formatting, packages_names)
        return_list = []

        for line in expac_return:
            splitted_line = line.split("?!")
            to_expand = {
                'name': splitted_line[0],
                'version': splitted_line[1],
                'depends': splitted_line[2].split(),
                'conflicts': splitted_line[3].split(),
                'required_by': splitted_line[4].split(),
                'optdepends': splitted_line[5].split(),
                'provides': splitted_line[6].split(),
                'replaces': splitted_line[7].split()
            }

            if packages_type is PossibleTypes.AUR_PACKAGE or packages_type is PossibleTypes.DEVEL_PACKAGE:
                if is_devel(to_expand['name']):
                    type_to_set = PossibleTypes.DEVEL_PACKAGE
                else:
                    type_to_set = PossibleTypes.AUR_PACKAGE
            else:
                type_to_set = packages_type

            to_expand['type_of'] = type_to_set

            if splitted_line[8] == '(null)':
                to_expand['pkgbase'] = to_expand['name']
            else:
                to_expand['pkgbase'] = splitted_line[8]

            if len(splitted_line) >= 10:
                to_expand['install_reason'] = splitted_line[9]

            if to_expand['name'] in to_expand['conflicts']:
                to_expand['conflicts'].remove(to_expand['name'])

            return_list.append(Package(**to_expand))

        return return_list

    def __init__(self, name: str, version: str, depends: Sequence[str] = None, conflicts: Sequence[str] = None,
                 required_by: Sequence[str] = None, optdepends: Sequence[str] = None, provides: Sequence[str] = None,
                 replaces: Sequence[str] = None, pkgbase: str = None, install_reason: str = None,
                 makedepends: Sequence[str] = None, checkdepends: Sequence[str] = None, type_of: PossibleTypes = None):
        self.name = name  # %n
        self.version = version  # %v
        self.depends = depends  # %D
        self.conflicts = conflicts  # %H
        self.required_by = required_by  # %N (only useful for installed packages)
        self.optdepends = optdepends  # %o
        self.provides = provides  # %P
        self.replaces = replaces  # %R
        self.pkgbase = pkgbase  # %e
        self.install_reason = install_reason  # %w (only with -Q)
        self.makedepends = makedepends  # aur only
        self.checkdepends = checkdepends  # aur only
        self.type_of = type_of  # PossibleTypes Enum value

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name and self.version == other.version

    def __hash__(self):
        return hash((self.name, self.version))

    def __repr__(self):
        return "Name: {}, Version: {}".format(self.name, self.version)

    def relevant_deps(self) -> List[str]:
        """
        Fetches the relevant deps of this package.
        self.depends for not aur packages,
        otherwise also self.makedepends and self.checkdepends

        :return:
        """
        to_return = []

        if self.depends is not None:
            to_return.extend(self.depends)
        if self.makedepends is not None:
            to_return.extend(self.makedepends)
        if self.checkdepends is not None:
            to_return.extend(self.checkdepends)

        return to_return

    def solutions_for_dep_problem(self, visited_list: List[Union[str, 'Package']], current_solution: List['Package'],
                                  installed_system: 'System', upstream_system: 'System', only_unfulfilled_deps: bool) -> \
            List[Tuple[List['Package'], List[Union[str, 'Package']]]]:
        """
        Heart of this AUR helper. Algorithm for dependency solving.
        Also checks for conflicts, dep-cycles and topologically sorts the solutions.

        :param visited_list:            List containing the visited nodes for the solution.
                                        May be "names" or packages.
        :param current_solution:        The packages in the current solution.
                                        Always topologically sorted
        :param installed_system:        The system containing the installed packages
        :param upstream_system:         The system containing the known upstream packages
        :param only_unfulfilled_deps:   True (default) if one only wants to fetch unfulfilled deps packages, False otherwise
        :return:                        A list containing the solutions.
                                        Every solution is a tuple containing two items:
                                        First item:
                                        A list of topologically sorted packages.
                                        Second item:
                                        The visited list for the solution
        """
        if self in current_solution:
            return [(deepcopy(current_solution), deepcopy(visited_list))]

        # dep cycle
        if self in visited_list:
            return []

        # conflict
        if System(current_solution).conflicting_with(self):
            return []

        visited_list = deepcopy(visited_list)
        visited_list.append(self)
        solution_visited_list = [(deepcopy(current_solution), visited_list)]

        # AND - every dep has to be fulfilled
        for dep in self.relevant_deps():
            if only_unfulfilled_deps and installed_system.provided_by(dep):
                continue

            dep_providers = upstream_system.provided_by(dep)
            # dep not fulfillable, solutions not valid
            if not dep_providers:
                return []

            # OR - at least one of the dep providers needs to provide the dep
            finished_solutions = [solution_tuple for solution_tuple in solution_visited_list if
                                  dep in solution_tuple[1]]
            not_finished_solutions = [solution_tuple for solution_tuple in solution_visited_list if
                                      dep not in solution_tuple[1]]

            for solution_tuple in not_finished_solutions:
                solution_tuple[1].append(dep)

            solution_visited_list = finished_solutions
            for solution_tuple in not_finished_solutions:
                for dep_provider in dep_providers:
                    solution_visited_list.extend(
                        dep_provider.solutions_for_dep_problem(solution_tuple[1], solution_tuple[0], installed_system,
                                                               upstream_system, only_unfulfilled_deps))

        for solution_tuple in solution_visited_list:
            solution_tuple[0].append(self)

        return solution_visited_list
