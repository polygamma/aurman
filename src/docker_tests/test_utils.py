from subprocess import run, PIPE, DEVNULL


class CurrentTest:
    to_return: int = 0


def test_command(command: str, dir_to_execute: str = None):
    return_command = run(command, shell=True, stdout=DEVNULL, stderr=PIPE, universal_newlines=True, cwd=dir_to_execute)

    if return_command.returncode == 0:
        print("Success with: '{}'".format(command))
    else:
        print(return_command.stderr)
        print("Error with: '{}'".format(command))
        CurrentTest.to_return = 1
