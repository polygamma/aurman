import logging
from enum import Enum
from typing import Sequence, List

from aurman.own_exceptions import InvalidInput


class PacmanOperations(Enum):
    DATABASE = "database"
    QUERY = "query"
    REMOVE = "remove"
    SYNC = "sync"
    DEPTEST = "deptest"
    UPGRADE = "upgrade"
    FILES = "files"
    VERSION = "version"
    HELP = "help"
    AURMAN = "aurman"


# value tuple description:
#
# name of the option in the PacmanArgs object,
# number of arguments needed (2 means at least one),
# option valid for the operations in the tuple (empty tuple means valid for all)
pacman_options = {
    "r": ("root", 1, ()),
    "root": ("root", 1, ()),
    "v": ("verbose", 0, ()),
    "verbose": ("verbose", 0, ()),
    "cachedir": ("cachedir", 2, ()),
    "color": ("color", 1, ()),
    "debug": ("debug", 0, ()),
    "gpgdir": ("gpgdir", 1, ()),
    "hookdir": ("hookdir", 2, ()),
    "logfile": ("logfile", 1, ()),
    "noconfirm": ("noconfirm", 0, ()),
    "confirm": ("confirm", 0, ()),
    "force": ("force", 0, ()),
    "asdeps": ("asdeps", 0, ()),
    "asexplicit": ("asexplicit", 0, ()),
    "needed": ("needed", 0, ()),
    "ignore": ("ignore", 1, ()),
    "ignoregroup": ("ignoregroup", 1, ()),

    "s": ("search", 2, (PacmanOperations.SYNC,)),
    "search": ("search", 2, (PacmanOperations.SYNC,)),
    "u": ("sysupgrade", 0, (PacmanOperations.SYNC,)),
    "sysupgrade": ("sysupgrade", 0, (PacmanOperations.SYNC,)),
    "y": ("refresh", 0, (PacmanOperations.SYNC,)),
    "refresh": ("refresh", 0, (PacmanOperations.SYNC,)),
    "c": ("clean", 0, (PacmanOperations.SYNC,)),
    "clean": ("clean", 0, (PacmanOperations.SYNC,)),

    "noedit": ("noedit", 0, (PacmanOperations.AURMAN,)),
    "always_edit": ("always_edit", 0, (PacmanOperations.AURMAN,)),
    "show_changes": ("show_changes", 0, (PacmanOperations.AURMAN,)),
    "devel": ("devel", 0, (PacmanOperations.AURMAN,)),
    "deep_search": ("deep_search", 0, (PacmanOperations.AURMAN,)),
    "pgp_fetch": ("pgp_fetch", 0, (PacmanOperations.AURMAN,)),
    "keyserver": ("keyserver", 1, (PacmanOperations.AURMAN,)),
    "aur": ("aur", 0, (PacmanOperations.AURMAN,)),
    "repo": ("repo", 0, (PacmanOperations.AURMAN,)),
    "domain": ("domain", 1, (PacmanOperations.AURMAN,)),
    "solution_way": ("solution_way", 0, (PacmanOperations.AURMAN,)),
    "holdpkg": ("holdpkg", 2, (PacmanOperations.AURMAN,)),
    "holdpkg_conf": ("holdpkg_conf", 0, (PacmanOperations.AURMAN,)),
    "do_everything": ("do_everything", 0, (PacmanOperations.AURMAN,)),
    "optimistic_versioning": ("optimistic_versioning", 0, (PacmanOperations.AURMAN,))
}

pacman_operations = {
    "D": PacmanOperations.DATABASE,
    "database": PacmanOperations.DATABASE,
    "Q": PacmanOperations.QUERY,
    "query": PacmanOperations.QUERY,
    "R": PacmanOperations.REMOVE,
    "remove": PacmanOperations.REMOVE,
    "S": PacmanOperations.SYNC,
    "sync": PacmanOperations.SYNC,
    "T": PacmanOperations.DEPTEST,
    "deptest": PacmanOperations.DEPTEST,
    "U": PacmanOperations.UPGRADE,
    "upgrade": PacmanOperations.UPGRADE,
    "F": PacmanOperations.FILES,
    "files": PacmanOperations.FILES,
    "V": PacmanOperations.VERSION,
    "version": PacmanOperations.VERSION,
    "h": PacmanOperations.HELP,
    "help": PacmanOperations.HELP
}


class PacmanArgs:
    def __init__(self):
        """
        Contains the parsed parameters.
        The names of the variables in this class are the long names of the parameters
        e.g. refresh for -y or refresh for --refresh
        values are bools and lists, nothing else
        bools for parameters without arguments e.g. --needed, lists otherwise e.g. --cachedir
        """
        self.operation: PacmanOperations = None
        self.targets: Sequence[str] = []  # contains the targets, e.g. the packages
        self.invalid_args: List[str] = []  # contains unknown parameters

    def __repr__(self):
        return_string = ""

        for name, value in self.__dict__.items():
            if not value or name == "invalid_args":
                continue

            if name == "operation":
                return_string += " " + "--{}".format(value.value)

            elif name == "targets":
                return_string += " " + " ".join(value)

            else:
                if pacman_options[name][2] and self.operation not in pacman_options[name][2]:
                    continue

                if len(name) >= 2:
                    return_string += " " + "--{}".format(name)
                else:
                    return_string += " " + "-{}".format(name)
                if not isinstance(value, bool) and not pacman_options[name][1] == 0:
                    new_values = []
                    for val in value:
                        if " " in val:
                            new_values.append("'{}'".format(val))
                        else:
                            new_values.append(val)
                    return_string += " " + " ".join(new_values)
                # dirty hack for things like -yy or -cc
                elif not isinstance(value, bool):
                    if len(name) >= 2:
                        return_string += " " + "--{}".format(name)
                    else:
                        return_string += " " + "-{}".format(name)

        return return_string.strip()


def parse_pacman_args(args: Sequence[str]) -> 'PacmanArgs':
    """
    Own parsing. Fills a concrete instance of PacmanArgs

    :param args:    the args to parse
    :return:        the instance of PacmanArgs containing the parsed parameters
    """

    def append_operation(operation: str):
        if args_to_return.operation is not None:
            logging.error("Tried to define more than one operation")
            raise InvalidInput("Tried to define more than one operation")

        args_to_return.operation = pacman_operations[operation]
        return "targets", 2

    def append_bool(param: str):
        new_current_field = pacman_options[param][0]
        # dirty hack for things like -yy or -cc
        if hasattr(args_to_return, new_current_field):
            setattr(args_to_return, new_current_field, ['something'])
        else:
            setattr(args_to_return, new_current_field, True)
        return new_current_field, 0

    args_to_return = PacmanArgs()
    current_field = "targets"
    number_of_valid_arguments = 2

    for arg in args:
        arg_length = len(arg)
        if arg.startswith("-"):
            if arg.startswith("--"):
                dashes = 2
            else:
                dashes = 1
        else:
            dashes = 0
        arg = arg.replace("-", "", dashes)

        if dashes == 2:
            if arg_length < 4:
                logging.error("{} is too short".format(arg))
                raise InvalidInput("{} is too short".format(arg))

        elif dashes == 1:
            if arg_length < 2:
                logging.error("{} is too short".format(arg))
                raise InvalidInput("{} is too short".format(arg))

            if arg_length > 2:
                for i in range(0, len(arg) - 1):
                    curr_char = arg[i]
                    if curr_char in pacman_operations:
                        current_field, number_of_valid_arguments = append_operation(curr_char)
                    elif curr_char not in pacman_options or pacman_options[curr_char][1] != 0:
                        args_to_return.invalid_args.append(curr_char)
                    else:
                        current_field, number_of_valid_arguments = append_bool(curr_char)
                arg = arg[len(arg) - 1]
        else:
            if isinstance(getattr(args_to_return, current_field), bool) or number_of_valid_arguments < 2 and len(
                    getattr(args_to_return, current_field)) + 1 > number_of_valid_arguments:
                current_field = "targets"
                number_of_valid_arguments = 2

            getattr(args_to_return, current_field).append(arg)

        if dashes > 0:
            if arg in pacman_operations:
                current_field, number_of_valid_arguments = append_operation(arg)
            elif arg not in pacman_options:
                args_to_return.invalid_args.append(arg)
            elif pacman_options[arg][1] == 0:
                current_field, number_of_valid_arguments = append_bool(arg)
            else:
                current_field = pacman_options[arg][0]
                number_of_valid_arguments = pacman_options[arg][1]

                if not hasattr(args_to_return, current_field):
                    setattr(args_to_return, current_field, [])

    if args_to_return.operation is None:
        logging.error("No operation defined")
        raise InvalidInput("No operation defined")

    checked_fields = set()

    for pacman_option in pacman_options.values():
        current_field = pacman_option[0]
        if current_field in checked_fields:
            continue
        number_of_valid_arguments = pacman_option[1]

        if not hasattr(args_to_return, current_field):
            if number_of_valid_arguments == 0:
                setattr(args_to_return, current_field, False)
            else:
                setattr(args_to_return, current_field, [])
        else:
            if number_of_valid_arguments > 0 and not getattr(args_to_return, current_field):
                logging.error("Parameters for {} are needed".format(current_field))
                raise InvalidInput("Parameters for {} are needed".format(current_field))

        checked_fields.add(current_field)

    return args_to_return
