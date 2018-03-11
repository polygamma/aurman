from subprocess import run, DEVNULL
from sys import argv, exit

if __name__ == '__main__':
    exit(run(" ".join(argv[1:]), shell=True, stdout=DEVNULL, stderr=DEVNULL).returncode)
