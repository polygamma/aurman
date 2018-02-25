import logging
import threading
import time
from pyalpm import vercmp
from subprocess import run, DEVNULL
from typing import Tuple, Sequence

from aurman.aur_utilities import get_aur_info
from aurman.colors import color_string, Colors
from aurman.own_exceptions import InvalidInput


def search_and_print(names: Sequence[str], installed_system, pacman_params: str, repo: bool, aur: bool):
    """
    Searches for something and prints the results

    :param names:               The things to search for
    :param installed_system:    A system containing the installed packages
    :param pacman_params:       parameters for pacman as string
    :param repo:                search only in repo
    :param aur:                 search only in aur
    """
    if not names:
        return

    if not aur:
        run("pacman {}".format(pacman_params), shell=True)

    if not repo:
        found_names = set(ret_dict['Name'] for ret_dict in get_aur_info([names[0]], True))
        for i in range(1, len(names)):
            found_names &= set(ret_dict['Name'] for ret_dict in get_aur_info([names[i]], True))

        search_return = get_aur_info(found_names)

        for ret_dict in sorted(search_return, key=lambda x: int(x['NumVotes']), reverse=True):
            first_line = "aur/{} {} ({}, {})".format(ret_dict['Name'], ret_dict['Version'], ret_dict['NumVotes'],
                                                     ret_dict['Popularity'])
            if ret_dict['Name'] in installed_system.all_packages_dict:
                first_line += " [installed]"
            print(first_line)
            print("    {}".format(ret_dict['Description']))


def split_name_with_versioning(name: str) -> Tuple[str, str, str]:
    """
    Splits name with versioning into its parts.
    e.g. "gunnar>=1.3.3.7" -> ("gunnar", ">=", "1.3.3.7")

    :param name:    the name to split
    :return:        the parts of the name in a tuple
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


def strip_versioning_from_name(name: str) -> str:
    """
    Strips versioning from a name.
    e.g. "gunnar>=1.3.3.7" -> "gunnar"

    :param name:    the name to strip the versioning from
    :return:        the name without versioning
    """

    return split_name_with_versioning(name)[0]


def version_comparison(version1: str, comparison_operator: str, version2: str) -> bool:
    """
    Compares two versions.
    e.g. "1.1" ">=" "1.0" -> True

    :param version1:                Version1
    :param comparison_operator:     Comparison operator
    :param version2:                Version2
    :return:                        True if the conditional relationship holds, False otherwise
    """

    vercmp_return = int(vercmp(version1, version2))

    if vercmp_return < 0:
        return "<" in comparison_operator
    elif vercmp_return == 0:
        return "=" in comparison_operator
    else:
        return ">" in comparison_operator


def acquire_sudo():
    """
    sudo loop since we want sudo forever
    """

    def sudo_loop():
        while True:
            if run("sudo -v", shell=True, stdout=DEVNULL).returncode != 0:
                logging.error("acquire sudo failed")
            time.sleep(120)

    if run("sudo -v", shell=True).returncode != 0:
        logging.error("acquire sudo failed")
        raise InvalidInput("acquire sudo failed")
    t = threading.Thread(target=sudo_loop)
    t.daemon = True
    t.start()


def ask_user(question: str, default: bool) -> bool:
    """
    Asks the user a yes/no question.
    :param question:    The question to ask
    :param default:     The default answer, if user presses enter.
                        True for yes, False for no
    :return:            yes: True, no: False
    """

    yes = ["y"]
    no = ["n"]
    if default:
        yes.append("")
        choices = "Y/n"
    else:
        no.append("")
        choices = "N/y"

    while True:
        user_choice = str(input("{} {}: ".format(question, choices))).strip().lower()
        if user_choice in yes or user_choice in no:
            return user_choice in yes
        print(color_string((Colors.LIGHT_RED, "That was not a valid choice!")))
