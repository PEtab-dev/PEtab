from setuptools import setup, find_packages
import os
import sys


# Python version check. We need >= 3.6 due to e.g. f-strings
if sys.version_info < (3, 6):
    sys.exit('PEtab requires at least Python version 3.6')


# read a file
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


# read version from file
version_file = os.path.join('petab', 'version.py')
exec(read(version_file))  # pylint: disable=W0122 # nosec

ENTRY_POINTS = {
    'console_scripts': [
        'petablint = petab.petablint:main',
    ]
}

# project metadata
setup(name='petab',
        version=__version__,  # noqa: F821
      description='Parameter estimation tabular data',
      long_description=read('README.md'),
      long_description_content_type="text/markdown",
      author='The PEtab developers',
      author_email='daniel.weindl@helmholtz-muenchen.de',
      url='https://github.com/icb-dcm/petab',
      packages=find_packages(exclude=['doc*', 'test*']),
      install_requires=['numpy>=1.15.1',
                        'pandas>=0.23.4',
                        'matplotlib>=2.2.3',
                        'python-libsbml>=5.17.0',
                        'sympy',
                        'colorama'],
      tests_require=['flake8', 'pytest'],
      python_requires='>=3.6',
      entry_points=ENTRY_POINTS,
      )
