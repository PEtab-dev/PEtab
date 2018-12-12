from setuptools import setup, find_packages
import os
import sys

# Python version check. We need >= 3.6 due to e.g. f-strings
if sys.version_info < (3, 6):
    sys.exit('PEtab requires at least Python version 3.6')


# read a file
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


# project metadata
setup(name='petab',
      version='0.0.0a2',
      description='Parameter estimation tabular data',
      long_description=read('README.md'),
      author='The PEtab developers',
      author_email='daniel.weindl@helmholtz-muenchen.de',
      url='https://github.com/icb-dcm/petab',
      packages=find_packages(exclude=['doc*', 'test*']),
      scripts=['bin/petablint.py'],
      install_requires=['numpy>=1.15.1',
                        'pandas>=0.23.4',
                        'matplotlib>=2.2.3',
                        'python-libsbml>=5.17.0',
                        'sympy'],
      tests_require=['pytest'],
      python_requires='>=3.6'
      )
