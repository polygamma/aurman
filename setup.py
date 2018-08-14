"""aurman AUR helper

see: https://github.com/polygamma/aurman
"""

from codecs import open
from os import path

from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='aurman',

    version='2.17.6',  # do not forget to change this

    python_requires='>=3.7',

    description='Arch Linux AUR helper',

    long_description=long_description,

    url='https://github.com/polygamma/aurman',

    author='Jonni Westphalen',

    author_email='jonny.westphalen@googlemail.com',

    packages=find_packages('src', exclude=['unit_tests', 'docker_tests']),
    package_dir={'': 'src'},

    entry_points={
        'console_scripts': [
            'aurman=aurman.main:main',
            'aurmansolver=aurman.main_solver:main'
        ]
    },

    install_requires=['requests', 'regex', 'pyalpm', 'python_dateutil', 'feedparser']
)
