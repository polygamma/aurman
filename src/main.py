from classes import System, Package
from sys import argv

if __name__ == '__main__':
    packages_interested_in = argv[1:]
    only_unfulfilled_deps = True

    print("installed system fetching...")
    installed_system = System(System.get_installed_packages())

    print("upstream system fetching...")
    upstream_system = System(System.get_repo_packages())

    print("own packages fetching...")
    upstream_system.append_packages_by_name(packages_interested_in)
    concrete_packages = [upstream_system.all_packages_dict[package_name] for package_name in packages_interested_in]

    print("calculating solutions...")
    solutions = Package.dep_solving(concrete_packages, installed_system, upstream_system, only_unfulfilled_deps)

    chosen_solution = installed_system.validate_and_choose_solution(solutions, concrete_packages)

    installed_system.show_solution_differences_to_user(chosen_solution)
