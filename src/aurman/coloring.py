class Colors:
    """
    Class used for colored output
    """

    @staticmethod
    def concat_str(*args):
        return ''.join([str(arg) for arg in args])

    @staticmethod
    def strip_colors(string: str) -> str:
        """
        Strips coloring from a string

        :param string:  The string to strip the coloring from
        :return:        The string without coloring
        """

        while "\033[" in string:
            beginning_index = string.index("\033[")
            string = string.replace(string[beginning_index:string.index("m", beginning_index) + 1], '')
        return string

    BLACK = lambda *x: Colors.concat_str("\033[30m", *x, "\033[39m")
    RED = lambda *x: Colors.concat_str("\033[31m", *x, "\033[39m")
    GREEN = lambda *x: Colors.concat_str("\033[32m", *x, "\033[39m")
    YELLOW = lambda *x: Colors.concat_str("\033[33m", *x, "\033[39m")
    BLUE = lambda *x: Colors.concat_str("\033[34m", *x, "\033[39m")
    MAGENTA = lambda *x: Colors.concat_str("\033[35m", *x, "\033[39m")
    CYAN = lambda *x: Colors.concat_str("\033[36m", *x, "\033[39m")
    LIGHT_GRAY = lambda *x: Colors.concat_str("\033[37m", *x, "\033[39m")
    DARK_GRAY = lambda *x: Colors.concat_str("\033[90m", *x, "\033[39m")
    LIGHT_RED = lambda *x: Colors.concat_str("\033[91m", *x, "\033[39m")
    LIGHT_GREEN = lambda *x: Colors.concat_str("\033[92m", *x, "\033[39m")
    LIGHT_YELLOW = lambda *x: Colors.concat_str("\033[93m", *x, "\033[39m")
    LIGHT_BLUE = lambda *x: Colors.concat_str("\033[94m", *x, "\033[39m")
    LIGHT_MAGENTA = lambda *x: Colors.concat_str("\033[95m", *x, "\033[39m")
    LIGHT_CYAN = lambda *x: Colors.concat_str("\033[96m", *x, "\033[39m")
    WHITE = lambda *x: Colors.concat_str("\033[97m", *x, "\033[39m")
    BOLD = lambda *x: Colors.concat_str("\033[1m", *x, "\033[21m")


def aurman_status(string: str, new_line: bool = False, to_print: bool = True) -> str:
    """
    Generates an aurman status

    :param string:      The string for the status message
    :param new_line:    Whether to start with a newline or not
    :param to_print:    If the generated status should be printed
    :return:            The generated status
    """
    if not new_line:
        our_string = ""
    else:
        our_string = "\n"

    our_string += "{} {}".format(Colors.LIGHT_GREEN("~~"), string)

    if to_print:
        print(our_string)

    return our_string


def aurman_error(string: str, new_line: bool = False, to_print: bool = True) -> str:
    """
    Generates an aurman error

    :param string:      The string for the error message
    :param new_line:    Whether to start with a newline or not
    :param to_print:    If the generated error should be printed
    :return:            The generated error
    """
    if not new_line:
        our_string = ""
    else:
        our_string = "\n"

    our_string += "{} {}".format(Colors.RED("!!"), string)

    if to_print:
        print(our_string)

    return our_string


def aurman_note(string: str, new_line: bool = False, to_print: bool = True) -> str:
    """
    Generates an aurman note

    :param string:      The string for the note message
    :param new_line:    Whether to start with a newline or not
    :param to_print:    If the generated note should be printed
    :return:            The generated note
    """
    if not new_line:
        our_string = ""
    else:
        our_string = "\n"

    our_string += "{} {}".format(Colors.LIGHT_CYAN("::"), string)

    if to_print:
        print(our_string)

    return our_string


def aurman_question(string: str, new_line: bool = False, to_print: bool = True) -> str:
    """
    Generates an aurman question

    :param string:      The string for the question message
    :param new_line:    Whether to start with a newline or not
    :param to_print:    If the generated question should be printed
    :return:            The generated question
    """
    if not new_line:
        our_string = ""
    else:
        our_string = "\n"

    our_string += "{} {}".format(Colors.LIGHT_YELLOW("??"), string)

    if to_print:
        print(our_string)

    return our_string
