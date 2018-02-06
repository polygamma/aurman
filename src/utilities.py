from subprocess import run, PIPE, DEVNULL
import logging
import threading
import time


def ask_user(question, default):
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
        choices = " Y/n: "
    else:
        no.append("")
        choices = " N/y: "

    user_choice = "I am not really sure right now"
    while (user_choice not in yes) and (user_choice not in no):
        user_choice = str(input(question + choices)).strip().lower()

    return user_choice in yes


def split_name_with_versioning(name):
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


def strip_versioning_from_name(name):
    """
    Strips versioning from a name.
    e.g. "gunnar>=1.3.3.7" -> "gunnar"
    :param name:    the name to strip the versioning from
    :return:        the name without versioning
    """

    return split_name_with_versioning(name)[0]


def version_comparison(version1, comparison_operator, version2):
    """
    Compares two versions.
    e.g. "1.1" ">=" "1.0" -> True
    :param version1:                Version1
    :param comparison_operator:     Comparison operator
    :param version2:                Version2
    :return:                        True if the conditional relationship holds, False otherwise
    """

    vercmp_return = int(
        run("vercmp '" + version1 + "' '" + version2 + "'", shell=True, stdout=PIPE, universal_newlines=True).stdout)

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
            run("sudo -v", shell=True, stdout=DEVNULL)
            logging.debug("sudo acquired")
            time.sleep(120)

    run("sudo -v", shell=True)
    logging.debug("sudo acquired")
    t = threading.Thread(target=sudo_loop)
    t.daemon = True
    t.start()


def ask_user_install_packages(aur_packages_to_install, repo_packages_to_install):
    """
    Asks the user whether the specified packages should be installed.

    :param aur_packages_to_install:     List containing the aur packages to install
    :param repo_packages_to_install:    List containing the repo packages to install
    :return: True if the user wants to install the packages, False otherwise
    """
    print("AUR Packages: " + " ".join([package.name for package in aur_packages_to_install]))
    print("Repo Packages: " + " ".join([package.name for package in repo_packages_to_install]))
    return ask_user("Do you want to install these packages?", True)
