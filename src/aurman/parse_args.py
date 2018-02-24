import logging
from typing import Sequence, Dict, Tuple

from aurman.own_exceptions import InvalidInput

parameters = {
    ('S', 'sync', 'U', 'upgrade'): (
        'b', 'dbpath', 'r', 'root', 'v', 'verbose', 'arch', 'cachedir', 'color', 'config', 'debug', 'gpgdir', 'hookdir',
        'logfile', 'noconfirm', 'confirm', 'd', 'nodeps', 'assume-installed', 'dbonly', 'noprogressbar', 'noscriptlet',
        'p', 'print', 'print-format', 'force', 'asdeps', 'asexplicit', 'ignore', 'ignoregroup'
    ),
    ('S', 'sync'): (
        'y', 'refresh'
    ),
    ('aurman', 'S', 'sync'): (
        'u', 'sysupgrade', 'needed'
    ),
    ('aurman',): (
        'noedit', 'devel', 'pk', 'deep_search', 'pgp_fetch'
    )
}


def args_to_string(args: Dict) -> str:
    """
    Parsed arguments back to a string.

    Example:    {
                    "": ["a", "b"],
                    "a": ["anice"],
                    "ab": ["bnice"]
                }                           -> "a b -a anice --ab bnice"

    :param args:    The parsed args
    :return:        The parsed args as string
    """
    return_string = ""

    for arg in args:
        if len(arg) == 0:
            return_string += " ".join(args[arg]) + " "
        elif len(arg) == 1:
            to_join = ["-" + arg]
            to_join.extend(args[arg])
            return_string += " ".join(to_join) + " "
        else:
            to_join = ["--" + arg]
            to_join.extend(args[arg])
            return_string += " ".join(to_join) + " "

    return return_string.strip()


def group_args(args: Sequence[str]) -> Tuple[str, Dict]:
    """
    Parses and groups args.

    Finds the operation specified in the args.
    See: https://www.archlinux.org/pacman/pacman.8.html
    There has to be exactly one operation, otherwise an Exception is being raised.

    A dict of the following format is being returned:
    {'aurman': {}, 'S': {}, 'U': {}, 'other': {}}

    If the operation is NOT S or sync, all parsed arguments except for the operation itself
    are listed under 'other'.

    Otherwise the parsed arguments except for the operation
    are grouped to 'aurman', 'S', 'U' and 'other' after the definition of "parameters".

    Two examples:
    "-Syu --packages a b --needed" ->   {
                                            'aurman': {"u": [], "packages": ["a", "b"], "needed": []},
                                            'S': {"y": [], "u": [], "needed": []},
                                            'U': {},
                                            'other': {}
                                        }

    "--remove -sc --gg a" ->            {
                                            'aurman': {},
                                            'S': {},
                                            'U': {},
                                            'other': {"s": [], "c": [], "gg": ["a"]}
                                        }

    :param args:    The arguments to parse as list.
    :return:        A tuple containing two items:
                    First: The operation specified
                    Second: The dict containing the grouped args except for the operation
    """

    parsed_args = parse_args(args)
    operations = [
        'D', 'database', 'Q', 'query', 'R', 'remove', 'S', 'sync', 'T', 'deptest', 'U', 'upgrade', 'F', 'files', 'V',
        'version', 'h', 'help'
    ]
    operation_found = None

    for operation in operations:
        if operation in parsed_args:
            if operation_found is not None:
                logging.error("Multiple operations defined in {}".format(args))
                raise InvalidInput("Multiple operations defined in {}".format(args))

            if parsed_args[operation]:
                logging.error("Operations with parameter in {}".format(args))
                raise InvalidInput("Operations with parameter in {}".format(args))

            operation_found = operation

    if operation_found is None:
        logging.error("No operation defined in {}".format(args))
        raise InvalidInput("No operation defined in {}".format(args))

    del parsed_args[operation_found]
    ordered_dict = {'aurman': {}, 'S': {}, 'U': {}, 'other': {}}

    for parsed_arg in parsed_args:
        for parameter in parameters:
            if operation_found not in ['S', 'sync']:
                ordered_dict['other'][parsed_arg] = parsed_args[parsed_arg]
                break

            values = parameters[parameter]
            if parsed_arg in values:
                if 'U' in parameter:
                    ordered_dict['U'][parsed_arg] = parsed_args[parsed_arg]
                if 'S' in parameter:
                    ordered_dict['S'][parsed_arg] = parsed_args[parsed_arg]
                if 'aurman' in parameter:
                    ordered_dict['aurman'][parsed_arg] = parsed_args[parsed_arg]
                break
        else:
            ordered_dict['other'][parsed_arg] = parsed_args[parsed_arg]

    return operation_found, ordered_dict


def parse_args(args: Sequence[str]) -> Dict:
    """
    Parses arguments.
    No positional arguments allowed. All parameters belong to the
    last specified argument. Returned is a dict containing
    the arguments as keys and the parameters in a list as values.

    Two examples:
    "-Syu well --packages p1 p2 --needed -t a --nice" ->    {
                                                                "S": [],
                                                                "y": [],
                                                                "u": ["well"],
                                                                "packages": ["p1", "p2"],
                                                                "needed": [],
                                                                "t": ["a"],
                                                                "nice": []
                                                            }

    "-a a -a b" ->  {
                        "a": ["a", "b"]
                    }

    :param args:    The arguments to parse as list.
    :return:        The dict containing the parsed args.
    """

    return_dict = {}
    curr_param = None

    if len(args) == 0:
        return return_dict

    if not args[0].startswith('-'):
        logging.error("Parsing {} failed".format(args))
        raise InvalidInput("Parsing {} failed".format(args))

    for arg in args:
        if arg.endswith('-'):
            logging.error("Parsing {} failed".format(args))
            raise InvalidInput("Parsing {} failed".format(args))

        if arg.startswith('-'):
            if (curr_param not in return_dict) and (curr_param is not None):
                return_dict[curr_param] = []

            if arg[1] == '-':
                curr_param = arg.replace('-', '')
            else:
                for i in range(1, len(arg) - 1):
                    return_dict[arg[i]] = []
                curr_param = arg[len(arg) - 1]

        else:
            if curr_param not in return_dict:
                return_dict[curr_param] = [arg]
            else:
                return_dict[curr_param].append(arg)

    if curr_param not in return_dict:
        return_dict[curr_param] = []

    return return_dict
