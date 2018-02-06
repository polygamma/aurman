import json
import logging
import requests
from own_exceptions import InvalidInput, ConnectionProblem
from urllib.parse import quote_plus


def get_aur_info(package_names):
    """
    Fetches AUR infos for package_names via AurJson.
    https://wiki.archlinux.org/index.php/AurJson
    :param package_names:   The names of the packages in a list
    :return:                Return of AurJson as dict.
    """
    query_url = "https://aur.archlinux.org/rpc/?v=5&type=info"
    query_prefix = "&arg[]="

    for package_name in package_names:
        query_url += query_prefix + quote_plus(package_name)

    try:
        return json.loads(requests.get(query_url, timeout=5).text)
    except requests.exceptions.RequestException:
        logging.error("Connection problem while requesting AUR info for %s", str(package_names), exc_info=True)
        raise ConnectionProblem()
    except json.JSONDecodeError:
        logging.error("Decoding problem while requesting AUR info for %s", str(package_names), exc_info=True)
        raise InvalidInput()


def is_devel(name):
    """
    Checks if a given package is a development package
    :param name:    the name of the package
    :return:        True if it is a development package, False otherwise
    """
    # endings of development packages

    develendings = ["bzr", "git", "hg", "svn", "daily", "nightly"]

    for develending in develendings:
        if name.endswith("-" + develending):
            return True

    return False
