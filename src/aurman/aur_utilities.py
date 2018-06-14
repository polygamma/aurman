import json
import logging
from typing import Sequence, List, Dict
from urllib.parse import quote_plus

import requests

from aurman.own_exceptions import InvalidInput, ConnectionProblem
from aurman.parsing_config import AurmanConfig
from aurman.wrappers import split_query_helper

aur_domain = "https://aur.archlinux.org"
aur_timeout = 5


def get_aur_info(package_names: Sequence[str], search: bool = False, by_name: bool = False) -> List[Dict]:
    """
    Fetches AUR infos for package_names via AurJson.
    https://wiki.archlinux.org/index.php/AurJson

    :param package_names:   The names of the packages in a sequence
    :param search:          True if one wants to search instead of getting info
    :param by_name:         If one wants to search by name only
    :return:                A list containing the "results" values of the RPC answer.
    """

    max_query_length = 8000
    if not search:
        query_url = aur_domain + "/rpc/?v=5&type=info"
        query_prefix = "&arg[]="
    else:
        query_url = aur_domain + "/rpc/?v=5&type=search"
        if by_name:
            query_url += "&by=name"
        query_prefix = "&arg="
    query_url_length = len(query_url.encode("utf8"))
    query_prefix_length = len(query_prefix.encode("utf8"))

    # quote_plus needed for packages like libc++
    package_names = [quote_plus(package_name) for package_name in package_names]

    queries_parameters = split_query_helper(max_query_length, query_url_length, query_prefix_length, package_names)

    results_list = []
    for query_parameters in queries_parameters:
        try:
            results_list.extend(
                json.loads(
                    requests.get(
                        "{}{}".format(
                            query_url,
                            ''.join(["{}{}".format(query_prefix, parameter) for parameter in query_parameters])
                        ),
                        timeout=aur_timeout
                    ).text
                )['results']
            )
        except requests.exceptions.RequestException:
            logging.error("Connection problem while requesting AUR info for {}".format(package_names), exc_info=True)
            raise ConnectionProblem("Connection problem while requesting AUR info for {}".format(package_names))
        except json.JSONDecodeError:
            logging.error("Decoding problem while requesting AUR info for {}".format(package_names), exc_info=True)
            raise InvalidInput("Decoding problem while requesting AUR info for {}".format(package_names))

    return results_list


def is_devel(name: str) -> bool:
    """
    Checks if a given package is a development package
    :param name:    the name of the package
    :return:        True if it is a development package, False otherwise
    """

    # endings of development packages
    develendings = ["bzr", "git", "hg", "svn", "daily", "nightly"]

    for develending in develendings:
        if name.endswith("-{}".format(develending)):
            return True

    # devel packages names specified in the aurman config
    if 'devel_packages' in AurmanConfig.aurman_config:
        return name in AurmanConfig.aurman_config['devel_packages']

    return False
