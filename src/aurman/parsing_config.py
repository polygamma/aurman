import configparser
import logging
import os
from subprocess import run, DEVNULL
from typing import Tuple, Set, Dict

from aurman.coloring import aurman_error, Colors
from aurman.own_exceptions import InvalidInput


class AurmanConfig:
    aurman_config = None


def read_config() -> 'configparser.ConfigParser':
    """
    Reads the aurman config and returns it

    :return:    The aurman config
    """
    # config dir
    config_dir = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser(os.path.join("~", ".config"))),
                              "aurman")
    config_file = os.path.join(config_dir, "aurman_config")

    # create config dir if it does not exist
    if not os.path.exists(config_dir):
        if run("install -dm700 '{}'".format(config_dir), shell=True, stdout=DEVNULL, stderr=DEVNULL).returncode != 0:
            logging.error("Creating config dir of aurman failed")
            raise InvalidInput("Creating config dir of aurman failed")

    # create empty config if config does not exist
    if not os.path.isfile(config_file):
        with open(config_file, 'w') as configfile:
            configfile.write("")

    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_file)
    AurmanConfig.aurman_config = config
    return config


def packages_from_other_sources() -> Tuple[Set[str], Dict[str, str]]:
    """
    Returns the packages which should be installed
    from sources where they normally would not be installed from.

    :return:        A tuple containing two items:
                        First item:
                            Set containing the names of packages to install from the aur

                        Second item:
                            Dict containing names from known repo packages as keys
                            and the repo to install those packages from as values
    """
    config = AurmanConfig.aurman_config
    if config is None:
        aurman_error("aurman config not loaded")
        raise InvalidInput("aurman config not loaded")

    aur_set = set()
    if 'aur_packages' in config:
        for aur_package_name in config['aur_packages']:
            aur_set.add(aur_package_name)

    repo_dict = {}
    if 'repo_packages' in config:
        for repo_package_name in config['repo_packages']:
            if config['repo_packages'][repo_package_name] is None:
                continue

            repo_dict[repo_package_name] = str(config['repo_packages'][repo_package_name])

    for name in aur_set:
        if name in repo_dict:
            aurman_error("Package {} listed for aur and repo.".format(Colors.BOLD(Colors.LIGHT_MAGENTA(name))))
            raise InvalidInput("Package {} listed for aur and repo.".format(Colors.BOLD(Colors.LIGHT_MAGENTA(name))))

    return aur_set, repo_dict
