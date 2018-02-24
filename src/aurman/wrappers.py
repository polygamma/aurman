import logging
from subprocess import run, PIPE, DEVNULL
from typing import Sequence, List

from aurman.own_exceptions import InvalidInput


def split_query_helper(max_length: int, base_length_of_query: int, length_per_append: int, to_append: Sequence[str]) -> \
        List[List[str]]:
    """
    Helper for splitting long queries.

    :param max_length:              The max length of a query
    :param base_length_of_query:    The base length of the query, e.g. length of expac -S '...'
    :param length_per_append:       A constant which is being added to the query length for every append of a parameter
                                    e.g. 1 for a space
    :param to_append:               A sequence containing the parameters as str
    :return:                        A list of lists
                                    where the inner lists contain the parameters for a single query
                                    len(return_value) yields the number of queries which have to be done all in all
    """
    current_query_length = base_length_of_query
    current_list = []
    return_list = [current_list]

    for append in to_append:
        append_length = len(append.encode("utf8"))
        if current_query_length + append_length + length_per_append <= max_length:
            current_list.append(append)
            current_query_length += append_length + length_per_append
        else:
            current_list = [append]
            return_list.append(current_list)
            current_query_length = base_length_of_query + append_length + length_per_append

        if current_query_length > max_length:
            logging.error("Query too long because of '{}'".format(append))
            raise InvalidInput("Query too long because of '{}'".format(append))

    return return_list


def expac(option: str, formatting: Sequence[str], targets: Sequence[str]) -> List[str]:
    """
    expac wrapper. see: https://github.com/falconindy/expac
    provide "option", "formatting" and "targets" as in this example:

    option as string: "-S"
    formatting as sequence containing strings: ("n", "v")
    targets as sequence containing strings: ("package1", "package2")

    :param option:      option as in https://github.com/falconindy/expac
    :param formatting:  formatting as in https://github.com/falconindy/expac
    :param targets:     sequence containing strings as targets as in https://github.com/falconindy/expac
    :return:            list containing the lines of the expac output.
                        one line of output is one item in the list.
                        the formatters are joined by '?!', so ('n', 'v') becomes %n?!%v in the output
    """

    max_query_length = 131071
    expac_base_query = "expac {} '{}'".format(option, "?!".join(["%{}".format(formatter) for formatter in formatting]))
    base_query_length = len(expac_base_query.encode("utf8"))
    queries_parameters = split_query_helper(max_query_length, base_query_length, 1, targets)

    return_list = []

    for query_parameters in queries_parameters:
        query = "{}{}".format(expac_base_query, ''.join([" {}".format(parameter) for parameter in query_parameters]))
        expac_return = run(query, shell=True, stdout=PIPE, stderr=DEVNULL, universal_newlines=True)
        if expac_return.returncode != 0:
            logging.error("expac query {} failed".format(query))
            raise InvalidInput("expac query {} failed".format(query))

        return_list.extend(expac_return.stdout.strip().splitlines())

    return return_list


def pacman(options_as_string: str, fetch_output: bool, dir_to_execute: str = None, sudo: bool = True) -> List[str]:
    """
    pacman wrapper. see: https://www.archlinux.org/pacman/pacman.8.html
    provide the pacman options as string via "options_as_string".
    e.g. "-Syu package1 package2"

    :param options_as_string:   the pacman options as string
    :param fetch_output:        True if you want to receive the output of pacman, False otherwise
    :param dir_to_execute:      if you want to execute the pacman command in a specific directory, provide the directory
    :param sudo:                True if you want to execute pacman with sudo, False otherwise
    :return:                    empty list in case of "fetch_output"=False, otherwise the lines of the pacman output as list.
                                one line of output is one item in the list.
    """
    if sudo:
        pacman_query = "sudo pacman {}".format(options_as_string)
    else:
        pacman_query = "pacman {}".format(options_as_string)

    if fetch_output:
        if dir_to_execute is not None:
            pacman_return = run(pacman_query, shell=True, stdout=PIPE, stderr=DEVNULL, universal_newlines=True,
                                cwd=dir_to_execute)
        else:
            pacman_return = run(pacman_query, shell=True, stdout=PIPE, stderr=DEVNULL, universal_newlines=True)
    else:
        if dir_to_execute is not None:
            pacman_return = run(pacman_query, shell=True, cwd=dir_to_execute)
        else:
            pacman_return = run(pacman_query, shell=True)

    if pacman_return.returncode != 0:
        logging.error("pacman query {} failed".format(pacman_query))
        raise InvalidInput("pacman query {} failed".format(pacman_query))

    if fetch_output:
        return pacman_return.stdout.strip().splitlines()

    return []


def makepkg(options_as_string: str, fetch_output: bool, dir_to_execute: str) -> List[str]:
    """
    makepkg wrapper. see: https://www.archlinux.org/pacman/makepkg.8.html
    provide the makepkg options as string via "options_as_string".
    e.g. "--printsrcinfo"

    :param options_as_string:   the makepkg options as string
    :param fetch_output:        True if you want to receive the output of makepkg, False otherwise
    :param dir_to_execute:      provide the directory in which the makepkg command should be executed
    :return:                    empty list in case of "fetch_output"=False, otherwise the lines of the makepkg output as list.
                                one line of output is one item in the list.
    """
    makepkg_query = "makepkg {}".format(options_as_string)
    if fetch_output:
        makepkg_return = run(makepkg_query, shell=True, stdout=PIPE, stderr=DEVNULL, universal_newlines=True,
                             cwd=dir_to_execute)
    else:
        makepkg_return = run(makepkg_query, shell=True, cwd=dir_to_execute)

    if makepkg_return.returncode != 0:
        logging.error("makepkg query {} failed".format(makepkg_query))
        raise InvalidInput("makepkg query {} failed".format(makepkg_query))

    if fetch_output:
        return makepkg_return.stdout.strip().splitlines()

    return []
