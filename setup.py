from setuptools import setup, find_packages
import os


# read a file
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


# project metadata
setup(name='petab',
      version='0.0.0',
      description="Parameter estimation tabular data",
      long_description=read('README.md'),
      author="The PEtab developers",
      author_email="",
      url="https://github.com/icb-dcm/petab",
      packages=find_packages(exclude=["doc*", "test*"]),
      scripts=['bin/petablint.py'],
      install_requires=['numpy>=1.15.1',
                        'pandas>=0.23.4',
                        'matplotlib>=2.2.3',
                        'sympy'],
      tests_require=['pytest']
      )
