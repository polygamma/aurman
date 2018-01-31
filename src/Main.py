import Utils
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(funcName)s - %(levelname)s - %(message)s')

if __name__ == '__main__':
    Utils.install_packages(sys.argv[1:])
