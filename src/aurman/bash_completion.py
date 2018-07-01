from subprocess import run, PIPE, DEVNULL
from sys import argv
from typing import List

from aurman.aur_utilities import get_aur_info
from aurman.parse_args import pacman_options


def possible_completions():
    if argv[3] == "--auto_complete_index":
        cur: str = ''
        index: int = int(argv[4]) - 1
        line: List[str] = argv[7:]
    else:
        cur: str = argv[3]
        index: int = int(argv[5]) - 1
        line: List[str] = argv[8:]

    for word in line:
        # sync operation is for us, everything else is not
        if word.startswith("-") and "S" in word or word == "--sync":
            break
    else:
        print("call_pacman")
        return

    # fetch valid options
    options = []
    for option in pacman_options:
        if len(option) == 1:
            options.append("-{}".format(option))
        else:
            options.append("--{}".format(option))

    # show options
    if cur.startswith("-"):
        # remove already used options
        for word in line:
            if not word.startswith("-"):
                continue

            if word.startswith("--"):
                if word in options:
                    options.remove(word)
                continue

            values = word[1:]
            for value in values:
                if "-{}".format(value) in options:
                    options.remove("-{}".format(value))

        print(" ".join(options))
        return

    # get valid option before cur
    option = None
    opt_index = None
    for i in reversed(range(0, index)):
        word = line[i]
        if not word.startswith("-"):
            continue

        if word.startswith("--"):
            if word in options:
                option = word.replace("-", "")
                opt_index = i
                break
            continue

        for value in reversed(word[1:]):
            if "-{}".format(value) in options:
                option = value
                opt_index = i
                break

    # decide if we can show the available sync packages or not
    if option is not None:
        option_num_args = pacman_options[option][1]
        if option_num_args == 2 or (index - opt_index) <= option_num_args:
            return

    results = run(
        ["expac", "-Ss", "%n", "^{}".format(cur)], stdout=PIPE, stderr=DEVNULL, universal_newlines=True
    ).stdout.splitlines()

    results.extend([ret_dict["Name"] for ret_dict in get_aur_info((cur,), True, True)])

    print(" ".join(results))
