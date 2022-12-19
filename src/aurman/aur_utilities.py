import json
import logging
from typing import Sequence, List, Dict
from urllib.error import URLError
from urllib.parse import quote_plus
from urllib.request import urlopen

from aurman.coloring import Colors, aurman_error
from aurman.own_exceptions import InvalidInput, ConnectionProblem
from aurman.parsing_config import AurmanConfig
from aurman.utilities import SearchSortBy
from aurman.wrappers import split_query_helper


class AurVars:
    aur_domain: str = "https://aur.archlinux.org"
    aur_timeout: int = 5


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
        query_url = AurVars.aur_domain + "/rpc/?v=5&type=info"
        query_prefix = "&arg[]="
    else:
        query_url = AurVars.aur_domain + "/rpc/?v=5&type=search"
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
            url = "{}{}".format(
                query_url,
                ''.join(["{}{}".format(query_prefix, parameter) for parameter in query_parameters])
            )
            with urlopen(url, timeout=AurVars.aur_timeout) as response:
                results_list.extend(json.loads(response.read())['results'])
        except URLError:
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


def search_and_print(names: Sequence[str], installed_system, pacman_params: 'PacmanArgs',
                     repo: bool, aur: bool, sort_by: SearchSortBy):
    """
    Searches for something and prints the results

    :param names:               The things to search for
    :param installed_system:    A system containing the installed packages
    :param pacman_params:       parameters for pacman as string
    :param repo:                search only in repo
    :param aur:                 search only in aur
    :param sort_by:             according to which the results are to be sorted
    """
    if not names:
        return

    if not aur:
        run(["pacman"] + pacman_params.args_as_list())

    if not repo:
        if sort_by is None:
            sort_by = SearchSortBy.POPULARITY

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
                aurman_error(
                    "Your query {} contains not enough non regex chars!".format(
                        Colors.BOLD(Colors.LIGHT_MAGENTA(name))
                    )
                )
                raise InvalidInput(
                    "Your query {} contains not enough non regex chars!".format(
                        Colors.BOLD(Colors.LIGHT_MAGENTA(name))
                    )
                )

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

        kwargs = {}
        if sort_by in [SearchSortBy.POPULARITY, SearchSortBy.VOTES]:
            kwargs.update(reverse=True)

        if sort_by is SearchSortBy.POPULARITY:
            kwargs.update(key=lambda x: float(x['Popularity']))
        elif sort_by is SearchSortBy.VOTES:
            kwargs.update(key=lambda x: int(x['NumVotes']))
        elif sort_by is SearchSortBy.NAME:
            kwargs.update(key=lambda x: str(x['Name']))

        for ret_dict in sorted(search_return, **kwargs):
            repo_with_slash = Colors.BOLD(Colors.LIGHT_MAGENTA("aur/"))
            name = Colors.BOLD(ret_dict['Name'])
            if ret_dict['OutOfDate'] is None:
                version = Colors.BOLD(Colors.GREEN(ret_dict['Version']))
            else:
                version = Colors.BOLD(Colors.RED(ret_dict['Version']))

            first_line = "{}{} {} ({}, {})".format(
                repo_with_slash, name, version, ret_dict['NumVotes'], ret_dict['Popularity']
            )
            if ret_dict['Name'] in installed_system.all_packages_dict:
                if version_comparison(
                        ret_dict['Version'], "=", installed_system.all_packages_dict[ret_dict['Name']].version
                ):
                    first_line += " {}".format(Colors.BOLD(Colors.CYAN("[installed]")))
                else:
                    first_line += " {}".format(
                        Colors.BOLD(Colors.CYAN("[installed: {}]".format(
                            installed_system.all_packages_dict[ret_dict['Name']].version
                        )))
                    )
            print(first_line)
            print("    {}".format(ret_dict['Description']))
