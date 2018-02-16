from typing import Sequence


class Colors:
    RESET = "\033[0m"
    DEFAULT = "\033[39m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    LIGHT_GRAY = "\033[37m"
    DARK_GRAY = "\033[90m"
    LIGHT_RED = "\033[91m"
    LIGHT_GREEN = "\033[92m"
    LIGHT_YELLOW = "\033[93m"
    LIGHT_BLUE = "\033[94m"
    LIGHT_MAGENTA = "\033[95m"
    LIGHT_CYAN = "\033[96m"
    WHITE = "\033[97m"


def color_string(args: Sequence[str]) -> str:
    """
    Concatenates the strings yielded by "args", finishes with Colors.RESET
    and returns that.

    :param args:    Sequence containing the strings to be concatenated and returned.
    :return:        The concatenated strings
    """
    return "{}{}".format(''.join(args), Colors.RESET)
