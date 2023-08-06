import logging
import shutil
import sys
import termios
import threading
import time
import tty
from enum import Enum, auto
from pyalpm import vercmp
from subprocess import run
from typing import Tuple, Sequence

import regex

from aurman.coloring import aurman_error, aurman_question
from aurman.own_exceptions import InvalidInput


class SudoLoop:
    # timeout for sudo loop
    timeout: int = 120
    interactive_command: [str] = ['sudo']
    noninteractive_command: [str] = ['sudo', '--non-interactive']
    test_interative: [str] = ['sudo', '-v']
    test_noninterative: [str] = ['sudo', '-v', '--non-interactive']


class SearchSortBy(Enum):
    # values to sort the -Ss results by
    NAME = auto()
    POPULARITY = auto()
    VOTES = auto()


def get_sudo_method():
    if SudoLoop.noninteractive_command:
        return SudoLoop.noninteractive_command
    return SudoLoop.interactive_command


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
    # prevent sudo_looping
    if SudoLoop.noninteractive_command == None \
            or SudoLoop.test_noninterative == None \
            or SudoLoop.test_interative == None:
        return

    def sudo_loop():
        while True:
            if run(SudoLoop.test_noninterative).returncode != 0:
                logging.error("acquire sudo failed")
            time.sleep(SudoLoop.timeout)

    if run(SudoLoop.test_interative).returncode != 0:
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
