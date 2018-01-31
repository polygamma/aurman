import Utils
import logging
import sys
import Exceptions

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(funcName)s - %(levelname)s - %(message)s')

if __name__ == '__main__':
    try:
        Utils.install_packages(sys.argv[1:])
    except (Exceptions.InvalidInput, Exceptions.ConnectionProblem):
        pass
