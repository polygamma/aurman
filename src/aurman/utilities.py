import logging
import sys
import termios
import threading
import time
import tty
from subprocess import run, DEVNULL, PIPE
from typing import Tuple, Sequence

import regex

from aurman.aur_utilities import get_aur_info
from aurman.coloring import Colors, aurman_error, aurman_question
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
        # escape for pacman
        to_escape = list("()+?|{}")
        for char in to_escape:
            pacman_params = pacman_params.replace(char, "\{}".format(char))

        run("pacman {}".format(pacman_params), shell=True)

    if not repo:
        # see: https://docs.python.org/3/howto/regex.html
        regex_chars = list("^.+*?$[](){}\|")

        regex_patterns = [regex.compile(name, regex.IGNORECASE) for name in names]
        names_beginnings_without_regex = []
        for name in names:
            index_start = -1
            index_end = len(name)
            for i, char in enumerate(name):
                if char not in regex_chars and index_start == -1:
                    index_start = i
                elif char in regex_chars and index_start != -1:
                    # must be at least two consecutive non regex chars
                    if i - index_start < 2:
                        index_start = -1
                        continue
                    index_end = i
                    break

            if index_start == -1 or index_end - index_start < 2:
                aurman_error("Your query {} "
                             "contains not enough non regex chars!"
                             "".format(Colors.BOLD(Colors.LIGHT_MAGENTA(name))))
                raise InvalidInput("Your query {} "
                                   "contains not enough non regex chars!"
                                   "".format(Colors.BOLD(Colors.LIGHT_MAGENTA(name))))

            names_beginnings_without_regex.append(name[index_start:index_end])

        found_names = set(ret_dict['Name'] for ret_dict in get_aur_info([names_beginnings_without_regex[0]], True)
                          if regex_patterns[0].findall(ret_dict['Name'])
                          or isinstance(ret_dict['Description'], str)
                          and regex_patterns[0].findall(ret_dict['Description']))

        for i in range(1, len(names)):
            found_names &= set(ret_dict['Name'] for ret_dict in get_aur_info([names_beginnings_without_regex[i]], True)
                               if regex_patterns[i].findall(ret_dict['Name'])
                               or isinstance(ret_dict['Description'], str)
                               and regex_patterns[i].findall(ret_dict['Description']))

        search_return = get_aur_info(found_names)

        for ret_dict in sorted(search_return, key=lambda x: float(x['Popularity']), reverse=True):
            repo_with_slash = Colors.BOLD(Colors.LIGHT_MAGENTA("aur/"))
            name = Colors.BOLD(ret_dict['Name'])
            if ret_dict['OutOfDate'] is None:
                version = Colors.BOLD(Colors.GREEN(ret_dict['Version']))
            else:
                version = Colors.BOLD(Colors.RED(ret_dict['Version']))

            first_line = "{}{} {} ({}, {})".format(repo_with_slash, name, version, ret_dict['NumVotes'],
                                                   ret_dict['Popularity'])
            if ret_dict['Name'] in installed_system.all_packages_dict:
                if version_comparison(ret_dict['Version'],
                                      "=",
                                      installed_system.all_packages_dict[ret_dict['Name']].version):
                    first_line += " {}".format(Colors.BOLD(Colors.CYAN("[installed]")))
                else:
                    first_line += " {}".format(Colors.BOLD(
                        Colors.CYAN("[installed: {}]"
                                    "".format(installed_system.all_packages_dict[ret_dict['Name']].version))))
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

    vercmp_return = int(run("vercmp '{}' '{}'".format(version1, version2), shell=True, stdout=PIPE, stderr=DEVNULL,
                            universal_newlines=True).stdout.strip())

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


def ask_user(question: str, default: bool, new_line: bool = False) -> bool:
    """
    Asks the user a yes/no question.
    :param question:    The question to ask
    :param default:     The default answer, if user presses enter.
                        True for yes, False for no
    :param new_line:    If new_line before printing the question
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
        print(aurman_question("{} {}: ".format(question, choices), new_line=new_line, to_print=False),
              end='', flush=True)

        # see https://stackoverflow.com/a/36974338
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setcbreak(fd)
            answer = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        print(flush=True)
        user_choice = answer.strip().lower()
        if user_choice in yes or user_choice in no:
            return user_choice in yes
        aurman_error("That was not a valid choice!")
