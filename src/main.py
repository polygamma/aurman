from classes import System, Package
from colors import color_string, Colors

if __name__ == '__main__':
    packages_interested_in = ["ros-indigo-desktop-full"]
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
    print("found {} solution(s)...\n".format(len(solutions)))
    for i, solution in enumerate(solutions, start=1):
        print(color_string((Colors.MAGENTA, "Solution {}: {}".format(i, solution))))

    print("\ncalculating new systems...")
    new_systems = [installed_system.hypothetical_append_packages_to_system(solution) for solution in solutions]
    print("validating new systems...")
    valid_systems = []
    valid_solutions_indices = []
    for i, new_system in enumerate(new_systems):
        for package in concrete_packages:
            if package.name not in new_system.all_packages_dict:
                break
        else:
            valid_systems.append(new_system)
            valid_solutions_indices.append(i)

    print("finding differences between systems...\n")
    systems_differences = installed_system.differences_between_systems(valid_systems)

    if len(valid_systems) > 1:
        if systems_differences[0][0]:
            print("new installed packages in all solutions:")
            print(color_string((Colors.GREEN, str(systems_differences[0][0]))))
        if systems_differences[0][1]:
            print("uninstalled packages in all solutions:")
            print(color_string((Colors.RED, str(systems_differences[0][1]))))
    elif len(valid_systems) == 1:
        if systems_differences[0][0]:
            print("new installed packages for the solution:")
            print(color_string((Colors.GREEN, str(systems_differences[0][0]))))
        if systems_differences[0][1]:
            print("uninstalled packages for the solution:")
            print(color_string((Colors.RED, str(systems_differences[0][1]))))
    else:
        print(color_string((Colors.RED, "No valid solutions found!")))

    print("\n")
    for i, difference_tuple in enumerate(systems_differences[1]):
        if difference_tuple[0] or difference_tuple[1]:
            print(color_string((Colors.LIGHT_CYAN,
                                "Solution {}\ninstalled: {}\nuninstalled: {}\n".format(valid_solutions_indices[i] + 1,
                                                                                       difference_tuple[0],
                                                                                       difference_tuple[1]))))
