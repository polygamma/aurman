from typing import Sequence, List
from enum import Enum, auto
from wrappers import expac
from aur_utilities import is_devel, get_aur_info


class PossibleTypes(Enum):
    REPO_PACKAGE = auto()
    AUR_PACKAGE = auto()
    DEVEL_PACKAGE = auto()
    PACKAGE_NOT_REPO_NOT_AUR = auto()


class Package:
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
